import openai
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from core.models import Recipe, Ingredient, UserPantry

openai.api_key = settings.OPENAI_API_KEY


def build_ai_recipe_context(user):
    """Builds structured user + pantry context for AI prompt."""
    profile = UserProfile.objects.get(user=user)
    pantry_items = (
        UserPantry.objects
        .filter(user=user, expiry_date__gte=timezone.now().date(), quantity__gt=0)
        .select_related("ingredient")
    )
    expiring_soon = [
        item for item in pantry_items if item.expiry_date <= timezone.now().date() + timedelta(days=3)
    ]

    return {
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
                "quantity": item.quantity,
                "unit": item.unit,
                "expiry_date": str(item.expiry_date),
                "is_expiring_soon": item in expiring_soon,
            }
            for item in pantry_items
        ],
    }


def generate_ai_recipe_from_openai(user):
    """
    Sends user context + pantry data to OpenAI to generate a custom recipe.
    The AI returns recipe name, description, ingredients, and instructions.
    """

    context = build_ai_recipe_context(user)

    prompt = f"""
    You are a smart kitchen assistant helping users reduce food waste.
    Create one complete recipe using ONLY these ingredients:
    {context['pantry']}.
    Avoid allergens: {context['user']['allergies']}.
    The user’s goal is: {context['user']['goal']}.
    Suggest a healthy, budget-friendly meal, with:
    - Name
    - Description
    - Ingredients (with quantities)
    - Step-by-step Instructions
    - Cuisine and Difficulty level
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional nutritionist and chef."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    recipe_text = response.choices[0].message.content

    # Save to DB (minimal structure, can be parsed later if you wish)
    recipe = Recipe.objects.create(
        name=f"AI Recipe by {user.username}",
        description=recipe_text[:250],  # short preview
        ingredients=recipe_text,  # full text for now
        instructions=recipe_text,
        difficulty="medium",
        cuisine="other",
        created_by=user,
        is_ai_generated=True,
    )
    return recipe
