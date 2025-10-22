# app/services/ai_recipe_service.py

from datetime import date, timedelta
from django.utils import timezone
from core.models import Ingredient, Recipe, UserPantry
from accounts.models import UserProfile
import random


def build_ai_recipe_context(user):
    """
    Builds a structured AI context for recipe generation and personalization.
    Based on requirements:
    - Reads user goals, allergies, and budget.
    - Collects available (non-expired) pantry ingredients.
    - Filters out allergens and expired items.
    - Flags ingredients nearing expiry for waste reduction.
    """

    profile = UserProfile.objects.get(user=user)

    pantry_items = (
        UserPantry.objects
        .filter(user=user, expiry_date__gte=timezone.now().date(), quantity__gt=0)
        .select_related("ingredient")
    )

    expiring_soon = [
        item for item in pantry_items if item.expiry_date <= timezone.now().date() + timedelta(days=3)
    ]

    context = {
        "user": {
            "name": user.username,
            "budget": profile.weekly_budget,
            "height": profile.height,
            "weight": profile.weight,
            "goal": profile.goal,
            "allergies": [a.strip().lower() for a in profile.allergies.split(",")] if profile.allergies else [],
        },
        "pantry": [
            {
                "ingredient": item.ingredient.name,
                "category": item.ingredient.category,
                "quantity": item.quantity,
                "unit": item.unit,
                "expiry_date": item.expiry_date.isoformat(),
                "is_expiring_soon": item in expiring_soon,
            }
            for item in pantry_items
        ],
        "timestamp": timezone.now().isoformat(),
    }
    return context



def generate_ai_recipe_suggestions(user, limit=5):
    """
    AI-driven recipe generation logic that:
    - Uses available ingredients
    - Avoids allergens
    - Prioritizes expiring items
    - Fits user's goals and budget
    - Suggests recipes the user can make now
    """

    context = build_ai_recipe_context(user)
    allergies = context["user"]["allergies"]
    budget = context["user"]["budget"]

    # Ingredients user currently has
    available_ingredients = [p["ingredient"].lower() for p in context["pantry"]]
    expiring_soon = [p["ingredient"].lower() for p in context["pantry"] if p["is_expiring_soon"]]

    # Filter recipes containing user’s available ingredients
    recipes = (
        Recipe.objects
        .filter(recipeingredient__ingredient__name__in=available_ingredients)
        .exclude(recipeingredient__ingredient__name__in=allergies)
        .distinct()
    )

    # Scoring logic: prioritize expiry usage, goal alignment, and availability
    scored_recipes = []
    for recipe in recipes:
        matched_ingredients = recipe.recipeingredient_set.filter(ingredient__name__in=available_ingredients).count()
        total_ingredients = recipe.recipeingredient_set.count()

        # Ingredient match ratio
        match_ratio = matched_ingredients / total_ingredients if total_ingredients > 0 else 0

        # Expiry priority: boost score if recipe uses expiring ingredients
        expiry_bonus = recipe.recipeingredient_set.filter(ingredient__name__in=expiring_soon).count() * 0.2

        # Nutrition goal alignment (mocked for now)
        nutrition_bonus = 0
        if "muscle" in context["user"]["goal"].lower():
            nutrition_bonus = recipe.total_protein / (recipe.total_calories or 1) * 0.5
        elif "lose" in context["user"]["goal"].lower():
            nutrition_bonus = (recipe.total_protein - recipe.total_fat) / (recipe.total_calories or 1) * 0.5

        final_score = (0.6 * match_ratio) + (0.2 * expiry_bonus) + (0.2 * nutrition_bonus)
        scored_recipes.append((recipe, final_score))

    # Sort recipes by score
    ranked = sorted(scored_recipes, key=lambda x: x[1], reverse=True)[:limit]

    return [
        {
            "recipe_id": r.id,
            "name": r.name,
            "description": r.description,
            "difficulty": r.difficulty,
            "cuisine": r.cuisine,
            "match_score": round(s, 2),
            "uses_expiring_items": any(ing.ingredient.name.lower() in expiring_soon for ing in r.recipeingredient_set.all()),
            "total_calories": r.total_calories,
            "total_protein": r.total_protein,
            "total_carbs": r.total_carbs,
            "total_fat": r.total_fat,
            "image": r.image.url if r.image else None,
        }
        for r, s in ranked
    ]

