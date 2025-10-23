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
    Generate a smart shopping list informed by pantry, recent AI recipes, budget, and user goals.
    Minimizes food waste and avoids allergens.
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
        - Pantry: {json.dumps([{'name': p.ingredient.name, 'quantity': float(p.quantity), 'unit': p.unit} for p in pantry])}
        - Expiring soon: {json.dumps([{'name': p.ingredient.name, 'quantity': float(p.quantity), 'unit': p.unit, 'expiry_date': str(p.expiry_date)} for p in expiring_soon])}
        - Missing ingredients for planned recipes: {json.dumps(missing_from_pantry)}

        Task:
        1. Generate a shopping list that covers missing ingredients first.
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

        # Save to DB
        with transaction.atomic():
            shopping_list = ShoppingList.objects.create(
                user=user,
                name=ai_json.get("list_name", "AI Smart Shopping List"),
                total_estimated_cost=Decimal(ai_json.get("total_estimated_cost", 0)),
                generated_at=timezone.now(),
                ai_generated=True,
            )

            for item in ai_json.get("items", []):
                ingredient_name = item.get("ingredient")
                if not ingredient_name:
                    continue

                ingredient_obj = Ingredient.objects.filter(name__iexact=ingredient_name.strip()).first()
                if not ingredient_obj:
                    ingredient_obj = Ingredient.objects.create(name=ingredient_name.strip(), category="other")

                ShoppingListItem.objects.create(
                    shopping_list=shopping_list,
                    ingredient=ingredient_obj,
                    quantity=item.get("quantity", 0),
                    unit=item.get("unit", "g"),
                    estimated_price=Decimal(item.get("estimated_price", 0)),
                    priority=item.get("priority", "medium"),
                    reason=item.get("reason", ""),
                )

            FoodWasteRecord.objects.create(
                user=user,
                shopping_list=shopping_list,
                predicted_waste=0,
                evaluation_status="pending"
            )

        return shopping_list

    except Exception as e:
        print(f"Error generating AI shopping list: {e}")
        return None
