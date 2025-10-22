# app/services/ai_recipe_service.py
import openai
import re
import json
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from core.models import Recipe, Ingredient, UserPantry

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
    Generate a complete recipe using OpenAI, based on user’s pantry and dietary data.
    Populates ALL recipe fields accurately.
    """
    context = build_ai_recipe_context(user)

    prompt = f"""
    You are a smart kitchen assistant helping users reduce food waste.

    Create ONE complete recipe in JSON format using ONLY these ingredients:
    {json.dumps(context['pantry'], indent=2)}

    Avoid allergens: {context['user']['allergies']}
    The user’s goal is: {context['user']['goal']}
    Preferred cuisines: {context['user']['preferred_cuisines']}

    Respond STRICTLY in this JSON structure:
    {{
        "name": "Recipe Name",
        "description": "A short appetizing summary",
        "cuisine": "One of: kenyan, italian, mexican, asian, indian, mediterranean, american, french, thai, chinese, japanese, other",
        "difficulty": "easy | medium | hard",
        "prep_time": 15,
        "cook_time": 25,
        "servings": 2,
        "ingredients": [
            {{"name": "Tomato", "quantity": 2, "unit": "pieces"}},
            {{"name": "Milk", "quantity": 200, "unit": "ml"}}
        ],
        "instructions": "Step-by-step cooking guide.",
        "total_calories": 520,
        "total_protein": 25,
        "total_carbs": 50,
        "total_fat": 20,
        "dietary_tags": "vegetarian, gluten-free"
    }}
    """

    try:
        # Send prompt to OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional nutritionist and chef."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )

        ai_content = response.choices[0].message.content.strip()

        # Extract JSON safely even if text contains extras
        match = re.search(r'\{.*\}', ai_content, re.DOTALL)
        recipe_json = json.loads(match.group()) if match else {}

        # Create Recipe instance with full data
        recipe = Recipe.objects.create(
            name=recipe_json.get("name", f"AI Recipe for {user.email}"),
            description=recipe_json.get("description", "No description available."),
            cuisine=recipe_json.get("cuisine", "other"),
            difficulty=recipe_json.get("difficulty", "medium"),
            prep_time=recipe_json.get("prep_time", 15),
            cook_time=recipe_json.get("cook_time", 25),
            servings=recipe_json.get("servings", 2),
            instructions=recipe_json.get("instructions", "Follow basic cooking steps."),
            total_calories=recipe_json.get("total_calories", 0),
            total_protein=recipe_json.get("total_protein", 0),
            total_carbs=recipe_json.get("total_carbs", 0),
            total_fat=recipe_json.get("total_fat", 0),
            dietary_tags=recipe_json.get("dietary_tags", ""),
            created_by=user,
            is_ai_generated=True,
        )

        # Match and add ingredients correctly
        ingredient_names = [i["name"].lower() for i in recipe_json.get("ingredients", [])]
        matched_ingredients = Ingredient.objects.filter(name__in=ingredient_names)

        recipe.ingredients.set(matched_ingredients)

        return recipe

    except Exception as e:
        print(f"Error generating AI recipe: {e}")
        return None
