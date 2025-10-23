# core/services/ai_shopping_service.py
import openai
import json
import re
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F

from accounts.models import UserProfile
from core.models import (
    Ingredient, UserPantry, ShoppingList, ShoppingListItem, Budget,
    UserGoal, Recipe, RecipeIngredient, FoodWasteRecord
)


# Embedded Food Waste Detection Logic
def detect_and_record_food_waste(user):
    """
    Detect food waste from UserPantry and create FoodWasteRecord entries.
    Criteria:
    - Items expired before being used => reason='expired'
    - Items with excessive remaining qty => reason='over_purchased'
    """
    today = timezone.now().date()
    pantry_items = UserPantry.objects.filter(user=user)

    for item in pantry_items:
        try:
            if item.status == 'inactive':
                continue

            # Expired and not used
            if item.expiry_date and item.expiry_date < today and item.quantity > 0:
                FoodWasteRecord.objects.create(
                    user=user,
                    ingredient=item.ingredient,
                    original_quantity=item.quantity,
                    quantity_wasted=item.quantity,
                    unit=item.unit,
                    cost=(item.price or Decimal("0.00")),
                    reason='expired',
                    reason_details="Item expired before being used",
                    purchase_date=item.purchase_date or today,
                    expiry_date=item.expiry_date or today,
                )
                item.status = 'inactive'
                item.save()

            # Over-purchased logic: check items in pantry for too long (> 21 days)
            elif item.purchase_date and (today - item.purchase_date).days > 21 and item.quantity > 0:
                FoodWasteRecord.objects.create(
                    user=user,
                    ingredient=item.ingredient,
                    original_quantity=item.quantity,
                    quantity_wasted=item.quantity * 0.5,  # assume half wasted
                    unit=item.unit,
                    cost=(item.price or Decimal("0.00")) * Decimal("0.5"),
                    reason='over_purchased',
                    reason_details="Item remained unused for 3+ weeks",
                    purchase_date=item.purchase_date or today,
                    expiry_date=item.expiry_date or today,
                )
                # reduce pantry stock
                item.quantity *= 0.5
                item.save()

        except Exception as e:
            print(f"Error detecting food waste for {item.ingredient.name}: {e}")


# AI Shopping List Generation Logic

def generate_ai_shopping_list(user, model="gpt-4o-mini", temperature=0.5):
    try:
        profile = UserProfile.objects.filter(user=user).first()
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        if not budget:
            raise ValueError("No active budget found for user.")

        pantry = UserPantry.objects.filter(user=user, quantity__gt=0).select_related("ingredient")
        expiring_soon = [
            p for p in pantry if p.expiry_date and p.expiry_date <= timezone.now().date() + timedelta(days=3)
        ]

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

        pantry_json = json.dumps([
            {"name": p.ingredient.name, "quantity": float(p.quantity), "unit": p.unit}
            for p in pantry
        ])
        expiring_json = json.dumps([
            {"name": p.ingredient.name, "quantity": float(p.quantity), "unit": p.unit, "expiry_date": str(p.expiry_date)}
            for p in expiring_soon
        ])
        missing_json = json.dumps(missing_from_pantry)
        allergies_json = json.dumps(allergies)

        prompt = (
            f"You are an AI grocery planner optimizing budget and minimizing food waste.\n\n"
            f"User context:\n"
            f"- Budget: {budget.amount} {budget.currency}\n"
            f"- Allergies (avoid): {allergies_json}\n"
            f"- Active goal: {goal_text}\n"
            f"- Pantry: {pantry_json}\n"
            f"- Expiring soon: {expiring_json}\n"
            f"- Missing ingredients for planned recipes: {missing_json}\n\n"
            f"Task:\n"
            f"1. Generate a shopping list that covers missing ingredients first.\n"
            f"2. Add staples if budget allows.\n"
            f"3. Stay below budget limit.\n"
            f"4. Avoid allergens and duplicates.\n"
            f"5. Prioritize ingredients helping to use expiring pantry items.\n"
            f"6. Include estimated cost for each item and total cost.\n\n"
            f"Respond ONLY with valid JSON."
        )

        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        ai_text = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        ai_json = json.loads(match.group()) if match else {}

        with transaction.atomic():
            sl = ShoppingList.objects.create(
                user=user,
                name=ai_json.get("list_name", "AI Smart Shopping List"),
                status="generated",
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
                    ing = Ingredient.objects.create(
                        name=name.strip(),
                        category="other",
                        common_units=item.get("unit", "g"),
                        calories=0.0, protein=0.0, carbs=0.0, fat=0.0, fiber=0.0
                    )

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



# Confirm Shopping List (includes waste detection)
def confirm_shopping_list(user, shopping_list_id, purchased_items_payload, total_actual_cost=None):
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

                if not sli and p.get("ingredient_name"):
                    ing = Ingredient.objects.filter(name__iexact=p["ingredient_name"].strip()).first()
                    sli = ShoppingListItem.objects.filter(shopping_list=sl, ingredient=ing).first() if ing else None

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
                        actual_price=Decimal(str(p.get("actual_price", 0) or 0)),
                    )
                else:
                    sli.purchased = True
                    if p.get("actual_price") is not None:
                        sli.actual_price = Decimal(str(p["actual_price"]))
                    if p.get("purchased_quantity") is not None:
                        sli.quantity = p["purchased_quantity"]
                    sli.save()

                actual_price = sli.actual_price if sli.actual_price is not None else sli.estimated_price
                total_spent += actual_price or Decimal("0.00")
                purchase_qty = sli.quantity or 0

                expiry_date = None
                if p.get("expiry_date"):
                    try:
                        expiry_date = timezone.datetime.strptime(p["expiry_date"], "%Y-%m-%d").date()
                    except Exception:
                        expiry_date = None

                UserPantry.objects.create(
                    user=user,
                    ingredient=sli.ingredient,
                    custom_name=sli.ingredient.name,
                    quantity=purchase_qty,
                    unit=sli.unit,
                    purchase_date=timezone.now().date(),
                    expiry_date=expiry_date if expiry_date else None,
                    price=actual_price or None,
                    status='active',
                )

            sl.status = "confirmed"
            sl.total_actual_cost = Decimal(str(total_actual_cost)) if total_actual_cost else total_spent
            sl.completed_at = timezone.now()
            sl.save()

        # etect food waste immediately after confirmation
        detect_and_record_food_waste(user)

        return sl

    except Exception as e:
        print(f"Error confirming shopping list: {e}")
        return None
