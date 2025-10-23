# core/services/ai_shopping_service.py
import openai
import json
import re
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from accounts.models import UserProfile
from core.models import (
    Ingredient, UserPantry, ShoppingList, ShoppingListItem, Budget,
    UserGoal, Recipe, RecipeIngredient, FoodWasteRecord
)


def generate_ai_shopping_list(user, model="gpt-4o-mini", temperature=0.5):
    """
    Generate a DRAFT AI shopping list (status='generated') informed by pantry, recent AI recipes, budget, and user goals.
    The list is *suggested* only — user must confirm purchases and record actual spend.
    Returns the created ShoppingList (draft) or None.
    """
    try:
        profile = UserProfile.objects.filter(user=user).first()
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        if not budget:
            raise ValueError("No active budget found for user.")

        pantry = UserPantry.objects.filter(user=user, quantity__gt=0).select_related("ingredient")
        expiring_soon = [
            p for p in pantry if p.expiry_date and p.expiry_date <= timezone.now().date() + timedelta(days=3)
        ]

        # recent AI recipes to derive missing ingredients
        recipes = Recipe.objects.filter(created_by=user, is_ai_generated=True).order_by('-created_at')[:3]
        pantry_names = [p.ingredient.name.lower() for p in pantry]

        recipe_ingredients = []
        for r in recipes:
            for ri in RecipeIngredient.objects.filter(recipe=r).select_related("ingredient"):
                recipe_ingredients.append({
                    "name": ri.ingredient.name,
                    "quantity": float(ri.quantity),
                    "unit": ri.unit
                })

        missing_from_pantry = [ri for ri in recipe_ingredients if ri["name"].lower() not in pantry_names]

        allergies = [a.strip().lower() for a in (profile.allergies or "").split(",") if a.strip()]
        goal = UserGoal.objects.filter(user=user, active=True).first()
        goal_text = goal.goal_type.replace("_", " ") if goal else "healthy eating"

        prompt = f"""
        You are an AI grocery planner optimizing budget and minimizing food waste.

        User context:
        - Budget: {budget.amount} {budget.currency}
        - Allergies (avoid): {allergies}
        - Active goal: {goal_text}
        - Pantry: {json.dumps([{{'name': p.ingredient.name, 'quantity': float(p.quantity), 'unit': p.unit}} for p in pantry])}
        - Expiring soon: {json.dumps([{{'name': p.ingredient.name, 'quantity': float(p.quantity), 'unit': p.unit, 'expiry_date': str(p.expiry_date)}} for p in expiring_soon])}
        - Missing ingredients for planned recipes: {json.dumps(missing_from_pantry)}

        Task:
        1. Generate a shopping list that covers missing ingredients first (for the planned recipes).
        2. Add complementary staples if budget allows.
        3. Stay below budget limit.
        4. Avoid allergens and duplicates.
        5. Prioritize ingredients helping to use expiring pantry items.
        6. Include estimated cost for each item and total cost.

        Respond ONLY with valid JSON:
        {{
            "list_name": "AI Smart Shopping List",
            "total_estimated_cost": number,
            "items": [
                {{
                    "ingredient": "name",
                    "quantity": number,
                    "unit": "g/ml/pieces",
                    "estimated_price": number,
                    "priority": "high|medium|low",
                    "reason": "why this was included"
                }}
            ]
        }}
        """

        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        ai_text = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        ai_json = json.loads(match.group()) if match else {}

        # Persist a DRAFT shopping list (status 'generated') — user must confirm later
        with transaction.atomic():
            sl = ShoppingList.objects.create(
                user=user,
                name=ai_json.get("list_name", "AI Smart Shopping List"),
                status="generated",                     # DRAFT status
                budget_limit=Decimal(str(budget.amount)),
                total_estimated_cost=Decimal(str(ai_json.get("total_estimated_cost", 0))),
                total_actual_cost=None,
                pantry_utilization=0.0,
                goal_alignment=0.0,
                waste_reduction_score=0.0,
                week_number=timezone.now().isocalendar()[1],
                month=timezone.now().month,
                year=timezone.now().year,
            )

            for item in ai_json.get("items", []):
                name = item.get("ingredient")
                if not name:
                    continue
                ing = Ingredient.objects.filter(name__iexact=name.strip()).first()
                if not ing:
                    ing = Ingredient.objects.create(name=name.strip(), category="other", common_units=item.get("unit", "g"),
                                                    calories=0.0, protein=0.0, carbs=0.0, fat=0.0, fiber=0.0)
                ShoppingListItem.objects.create(
                    shopping_list=sl,
                    ingredient=ing,
                    quantity=item.get("quantity", 0),
                    unit=item.get("unit", "g"),
                    estimated_price=Decimal(str(item.get("estimated_price", 0))),
                    priority=item.get("priority", "medium"),
                    notes=item.get("reason", ""),
                    purchased=False,
                )

        return sl

    except Exception as e:
        print(f"Error generating AI shopping list: {e}")
        return None


def confirm_shopping_list(user, shopping_list_id, purchased_items_payload, total_actual_cost=None):
    """
    Confirm a generated shopping list.

    purchased_items_payload: list of dicts with keys:
      - shopping_list_item_id (int) OR ingredient_name (str)
      - actual_price (decimal/float)
      - purchased_quantity (float)
      - expiry_date (YYYY-MM-DD) optional
      - expiry_label_image (optional file path or media reference) optional

    This function:
    - Marks ShoppingList.status -> 'confirmed' or 'completed'
    - Updates ShoppingListItem.purchased and actual_price
    - Creates UserPantry records for purchased items
    - Sets total_actual_cost on ShoppingList
    - Seeds a FoodWasteRecord placeholder (pending evaluation)
    """
    try:
        sl = ShoppingList.objects.select_for_update().get(id=shopping_list_id, user=user)
        if sl.status not in ("generated", "draft"):
            raise ValueError("Shopping list is not in a confirmable state.")

        with transaction.atomic():
            total_spent = Decimal("0.00")
            for p in purchased_items_payload:
                sli = None
                if p.get("shopping_list_item_id"):
                    sli = ShoppingListItem.objects.filter(id=p["shopping_list_item_id"], shopping_list=sl).first()
                # fallback by ingredient name
                if not sli and p.get("ingredient_name"):
                    ing = Ingredient.objects.filter(name__iexact=p["ingredient_name"].strip()).first()
                    sli = ShoppingListItem.objects.filter(shopping_list=sl, ingredient=ing).first() if ing else None

                # If item doesn't exist in SL, create it (user added manual buy)
                if not sli:
                    ing_name = p.get("ingredient_name") or "unknown"
                    ing = Ingredient.objects.filter(name__iexact=ing_name.strip()).first()
                    if not ing:
                        ing = Ingredient.objects.create(name=ing_name.strip(), category="other", calories=0.0,
                                                        protein=0.0, carbs=0.0, fat=0.0, fiber=0.0)
                    sli = ShoppingListItem.objects.create(
                        shopping_list=sl,
                        ingredient=ing,
                        quantity=p.get("purchased_quantity", p.get("quantity", 0) or 0),
                        unit=p.get("unit", "g"),
                        estimated_price=Decimal(str(p.get("estimated_price", 0))) if p.get("estimated_price") else Decimal("0.00"),
                        priority=p.get("priority", "medium"),
                        notes=p.get("notes", ""),
                        purchased=True,
                        actual_price=Decimal(str(p.get("actual_price", p.get("actual_price", 0) or 0))),
                    )
                else:
                    # Update existing shopping list item
                    sli.purchased = True
                    if p.get("actual_price") is not None:
                        sli.actual_price = Decimal(str(p.get("actual_price")))
                    if p.get("purchased_quantity") is not None:
                        sli.quantity = p.get("purchased_quantity")
                    sli.save()

                # Add to UserPantry
                actual_price = sli.actual_price if sli.actual_price is not None else sli.estimated_price
                total_spent += actual_price or Decimal("0.00")
                purchase_qty = sli.quantity or 0

                # expiry_date may be provided by frontend (e.g., Vision API processed)
                expiry_date = None
                if p.get("expiry_date"):
                    try:
                        expiry_date = timezone.datetime.strptime(p["expiry_date"], "%Y-%m-%d").date()
                    except Exception:
                        expiry_date = None

                # create or update pantry item (simple approach: create new entry)
                UserPantry.objects.create(
                    user=user,
                    ingredient=sli.ingredient,
                    custom_name=sli.ingredient.name,
                    quantity=purchase_qty,
                    unit=sli.unit,
                    purchase_date=timezone.now().date(),
                    expiry_date=expiry_date if expiry_date else (None),
                    price=actual_price or None,
                    status='active',
                )

                # If expiry_date is None and frontend uploaded an expiry_label_image, call Vision API here
                # to detect expiry_date and then update the created UserPantry entry accordingly.
                # (Placeholder for vision integration)

            # finalize shopping list
            sl.status = "confirmed"
            sl.total_actual_cost = Decimal(str(total_actual_cost)) if total_actual_cost is not None else total_spent
            sl.completed_at = timezone.now()
            sl.save()

            # seed FoodWasteRecord as pending evaluation (actual waste measured later)
            FoodWasteRecord.objects.create(
                user=user,
                ingredient=None,
                original_quantity=0,
                quantity_wasted=0,
                unit="",
                cost=sl.total_actual_cost or Decimal("0.00"),
                reason="pending_evaluation",
                purchase_date=timezone.now().date(),
                expiry_date=timezone.now().date(),
            )

        return sl

    except Exception as e:
        print(f"Error confirming shopping list: {e}")
        return None
