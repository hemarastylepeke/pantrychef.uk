# core/services/ai_recipe_service.py
import openai
import re
import json
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile, UserGoal
from core.models import Recipe, Ingredient, UserPantry, RecipeIngredient, Budget

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
                "quantity": float(item.quantity),
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
    Generate an AI-powered recipe suggestion based on:
    - Pantry ingredients,use what’s available
    - Dietary requirements (avoid allergies)
    - Goal (lose weight, build muscle, etc.)
    - Budget
    - Preferred cuisine
    - Difficulty, time, and adult portion size
    """
    try:
        profile = UserProfile.objects.get(user=user)
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        goal = UserGoal.objects.filter(user_profile__user=user, active=True).order_by('priority').first()

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

        # Comprehensive AI Prompt
        prompt = f"""
        You are an expert AI chef and nutritionist creating a personalized, balanced meal.
        
        User Context:
        - Goal: {goal_text}
        - Budget: {budget_text}
        - Allergies (strictly avoid): {allergies}
        - Preferred cuisines: {cuisines or ["any"]}
        - Pantry ingredients: {json.dumps(pantry_data, indent=2)}
        - Recently cooked recipes: {list(recent_recipes)}

        Your job:
        1. Use pantry ingredients as much as possible (especially those expiring soon).
        2. Avoid ingredients the user is allergic to.
        3. Suggest a recipe suitable for 1 adult portion size.
        4. Stay within the user’s budget range when suggesting new ingredients.
        5. Choose a cuisine from the user’s preferences (or any suitable one if none).
        6. Include difficulty level (easy, medium, hard) and total cooking time (prep + cook).
        7. The recipe must align with the user’s goal — e.g., high protein for muscle gain, low carb for weight loss.
        8. Avoid repeating recipes from the recent list.

        Return ONLY valid JSON structured as:
        {{
            "name": "Recipe Name",
            "description": "Brief appetizing summary",
            "cuisine": "kenyan | italian | mexican | asian | indian | mediterranean | american | other",
            "difficulty": "easy | medium | hard",
            "prep_time": number,
            "cook_time": number,
            "servings": 1,
            "ingredients": [
                {{"name": "IngredientName", "quantity": number, "unit": "g/ml/pieces"}}
            ],
            "instructions": "Step-by-step preparation guide",
            "total_calories": number,
            "total_protein": number,
            "total_carbs": number,
            "total_fat": number,
            "dietary_tags": "comma-separated tags like gluten-free, high-protein, low-fat"
        }}
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional AI chef focused on personalized, healthy meal planning."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
        )

        ai_text = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        recipe_json = json.loads(match.group()) if match else {}

        # Persist Recipe in DB
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

        # Link Ingredients from our db
        for ing in recipe_json.get("ingredients", []):
            name = ing.get("name")
            if not name:
                continue
            ingredient_obj = (
                Ingredient.objects.filter(name__iexact=name.strip()).first()
                or Ingredient.objects.create(
                    name=name.strip(),
                    category="other",
                    calories=0,
                    protein=0,
                    carbs=0,
                    fat=0,
                    fiber=0,
                )
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
