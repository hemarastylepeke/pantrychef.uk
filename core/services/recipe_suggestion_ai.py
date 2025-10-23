# app/services/ai_recipe_service.py
import openai
import re
import json
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from core.models import Recipe, Ingredient, UserPantry, RecipeIngredient, Budget, UserGoal

openai.api_key = settings.OPENAI_API_KEY


def build_ai_recipe_context(user):
    """Build structured user + pantry context for OpenAI recipe generation."""
    profile = UserProfile.objects.get(user=user)
    pantry_items = (
        UserPantry.objects
        .filter(user=user, expiry_date__gte=timezone.now().date(), quantity__gt=0)
        .select_related("ingredient")
    )

    expiring_soon = [
        item for item in pantry_items
        if item.expiry_date <= timezone.now().date() + timedelta(days=3)
    ]

    context = {
        "user": {
            "email": user.email,
            "first_name": profile.first_name or "",
            "height": profile.height or "Unknown",
            "weight": profile.weight or "Unknown",
            "goal": getattr(profile, "goal", "Healthy eating"),
            "allergies": [a.strip().lower() for a in profile.allergies.split(",")] if profile.allergies else [],
            "preferred_cuisines": [c.strip().lower() for c in profile.preferred_cuisines.split(",")] if profile.preferred_cuisines else [],
        },
        "pantry": [
            {
                "ingredient": item.ingredient.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "expiry_date": str(item.expiry_date),
                "is_expiring_soon": item in expiring_soon,
            }
            for item in pantry_items
        ],
    }
    return context


def generate_ai_recipe_from_openai(user):
    """
    Generate a complete recipe using OpenAI, based on user’s pantry, dietary, and budget context.
    Returns Recipe instance or None.
    """
    try:
        profile = UserProfile.objects.get(user=user)
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        goal = UserGoal.objects.filter(user=user, active=True).order_by('priority').first()

        recent_recipes = Recipe.objects.filter(
            created_by=user,
            created_at__gte=timezone.now() - timedelta(days=21)
        ).values_list('name', flat=True)

        pantry_qs = UserPantry.objects.filter(
            user=user, expiry_date__gte=timezone.now().date(), quantity__gt=0
        ).select_related("ingredient")

        expiring_soon = [
            p for p in pantry_qs if p.expiry_date <= timezone.now().date() + timedelta(days=3)
        ]

        pantry_data = [
            {
                "name": p.ingredient.name,
                "quantity": float(p.quantity),
                "unit": p.unit,
                "expiry_date": str(p.expiry_date),
                "is_expiring_soon": p in expiring_soon,
            }
            for p in pantry_qs
        ]

        allergies = [a.strip().lower() for a in (profile.allergies or "").split(",") if a.strip()]
        cuisines = [c.strip().lower() for c in (profile.preferred_cuisines or "").split(",") if c.strip()]
        goal_text = goal.goal_type.replace("_", " ") if goal else "general healthy eating"
        budget_text = f"{budget.amount} {budget.currency}" if budget else "unlimited"

        # Prompt for recipe generation
        prompt = f"""
        You are an expert AI chef creating a meal to reduce food waste and stay within a weekly budget.
        User context:
        - Goal: {goal_text}
        - Budget limit: {budget_text}
        - Allergies (avoid): {allergies}
        - Preferred cuisines: {cuisines}
        - Pantry items: {json.dumps(pantry_data, indent=2)}
        - Recently cooked recipes: {list(recent_recipes)}

        Your task:
        1. Create one unique, balanced, affordable recipe using mostly pantry items.
        2. Prefer using ingredients that are expiring soon.
        3. Avoid allergens and repeated dishes from recent recipes.
        4. Stay mindful of user’s goal (e.g., lose weight → low calorie, build muscle → high protein).
        5. Suggest quantities for 1 adult serving.

        Respond ONLY with valid JSON:
        {{
            "name": "Recipe Name",
            "description": "Short appetizing description",
            "cuisine": "kenyan | italian | mexican | asian | indian | mediterranean | american | other",
            "difficulty": "easy | medium | hard",
            "prep_time": number,
            "cook_time": number,
            "servings": number,
            "ingredients": [
                {{"name": "IngredientName", "quantity": number, "unit": "g/ml/pieces"}}
            ],
            "instructions": "Step-by-step guide",
            "total_calories": number,
            "total_protein": number,
            "total_carbs": number,
            "total_fat": number,
            "dietary_tags": "comma-separated tags"
        }}
        """

        # Send to OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional chef and nutritionist."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )

        ai_text = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        recipe_json = json.loads(match.group()) if match else {}

        # Save Recipe
        recipe = Recipe.objects.create(
            name=recipe_json.get("name", f"AI Recipe {timezone.now().strftime('%Y%m%d%H%M')}"),
            description=recipe_json.get("description", ""),
            cuisine=recipe_json.get("cuisine", "other"),
            difficulty=recipe_json.get("difficulty", "medium"),
            prep_time=recipe_json.get("prep_time", 15),
            cook_time=recipe_json.get("cook_time", 25),
            servings=recipe_json.get("servings", 1),
            instructions=recipe_json.get("instructions", ""),
            total_calories=recipe_json.get("total_calories", 0),
            total_protein=recipe_json.get("total_protein", 0),
            total_carbs=recipe_json.get("total_carbs", 0),
            total_fat=recipe_json.get("total_fat", 0),
            dietary_tags=recipe_json.get("dietary_tags", ""),
            created_by=user,
            is_ai_generated=True,
        )

        # Ingredients
        for ing in recipe_json.get("ingredients", []):
            name = ing.get("name")
            if not name:
                continue
            ingredient_obj, _ = Ingredient.objects.get_or_create(
                name__iexact=name.strip(),
                defaults={"name": name.strip(), "category": "other"}
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                quantity=ing.get("quantity", 0),
                unit=ing.get("unit", "g")
            )

        recipe.calculate_nutrition()
        return recipe

    except Exception as e:
        print(f"Error generating AI recipe: {e}")
        return None
