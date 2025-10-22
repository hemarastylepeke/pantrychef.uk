# core/services/ai_shopping_service.py

import openai
import json
import re
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from accounts.models import UserProfile
from core.models import (
    Ingredient, UserPantry, ShoppingList, ShoppingListItem, Budget, UserGoal, FoodWasteRecord
)

# ensure openai.api_key already set in your settings and client initialization elsewhere

def generate_ai_shopping_list(user, model="gpt-4o-mini", temperature=0.5):
    """
    Generate an AI shopping list that strictly respects:
      - user's active budget (Budget)
      - user's pantry (use existing items first)
      - user's allergies/dietary requirements (avoid them)
      - prioritizes expiring items (reduce waste)
      - aligns with user's goal (UserGoal)
    Returns the created ShoppingList or None on failure.
    """
    try:
        # 1) Fetch user context
        profile = UserProfile.objects.filter(user=user).first()
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        if not budget:
            raise ValueError("No active budget found for user. Please create a Budget entry.")

        pantry_qs = UserPantry.objects.filter(user=user, quantity__gt=0, status='active').select_related('ingredient')
        pantry_items = []
        expiring_items = set()
        for p in pantry_qs:
            pantry_items.append({
                "name": p.ingredient.name,
                "quantity": float(p.quantity),
                "unit": p.unit,
                "expiry_date": p.expiry_date.isoformat(),
                "is_expiring_soon": (p.expiry_date <= timezone.now().date() + timezone.timedelta(days=3))
            })
            if p.expiry_date <= timezone.now().date() + timezone.timedelta(days=3):
                expiring_items.add(p.ingredient.name.lower())

        goal = UserGoal.objects.filter(user=user, active=True).order_by('priority').first()
        goal_text = goal.goal_type.replace('_', ' ') if goal else "general healthy eating"

        allergies = []
        if profile and profile.allergies:
            allergies = [a.strip().lower() for a in profile.allergies.split(',') if a.strip()]

        # 2) Build strict prompt for AI (forces JSON)
        prompt = f"""
You are an AI grocery planner specialized in minimizing food waste and respecting diet & budget constraints.

User/context:
- Budget limit: {budget.amount} {budget.currency} (period={budget.period})
- Current pantry items (name | qty | unit | expiring soon): {json.dumps(pantry_items)}
- Allergies (do NOT suggest or recommend these): {allergies}
- Active goal: {goal_text}
- Objective: generate a shopping list that:
  * Complements existing pantry items,
  * Prioritizes using ingredients that are expiring soon (indicated in pantry),
  * Avoids user's allergens and disliked ingredients,
  * Stays within the budget limit (total_estimated_cost <= budget),
  * Is budget-efficient and minimizes likely waste.

Return STRICTLY and ONLY a valid JSON object (no commentary) with this exact schema:
{{
  "list_name": "AI Weekly Smart Shopping List",
  "total_estimated_cost": number,
  "items": [
    {{
      "ingredient": "Ingredient name",
      "quantity": number,
      "unit": "g/ml/pieces",
      "estimated_price": number,
      "priority": "high|medium|low",
      "reason": "short reason (e.g., complements pantry, expiring use, high protein)"
    }}
  ]
}}

Rules for the AI:
- The sum of estimated_price in items must NOT exceed the budget limit.
- Do NOT include any ingredient whose name matches any allergy (case-insensitive).
- Prefer items that help use expiring pantry items; call out in "reason" if it's to use expiring items.
- If budget prevents including all recommended items, recommend lower-priority items to drop but still return a JSON list with total_estimated_cost <= budget.
        """

        # 3) Call OpenAI
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a budget- and waste-aware grocery planner."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )

        ai_text = response.choices[0].message.content.strip()

        # 4) Extract JSON safely
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if not match:
            raise ValueError("AI did not return a JSON object.")
        ai_json = json.loads(match.group())

        # 5) Validate AI JSON structure
        items = ai_json.get("items", [])
        if not isinstance(items, list):
            raise ValueError("AI response invalid: 'items' must be a list.")

        # sanitize and enforce constraints
        sanitized_items = []
        total_cost = Decimal(0)
        for it in items:
            if not isinstance(it, dict):
                continue
            ing_name = (it.get("ingredient") or "").strip()
            if not ing_name:
                continue
            ing_name_low = ing_name.lower()
            # skip allergens
            if any(a == ing_name_low or a in ing_name_low for a in allergies):
                continue
            qty = float(it.get("quantity", 1))
            unit = it.get("unit", "g")
            est_price = Decimal(str(it.get("estimated_price", 0)))
            priority = it.get("priority", "medium")
            reason = it.get("reason", "")

            sanitized_items.append({
                "ingredient": ing_name,
                "quantity": qty,
                "unit": unit,
                "estimated_price": est_price,
                "priority": priority,
                "reason": reason
            })
            total_cost += est_price

        # Enforce budget: if AI returned higher cost, try to trim low-priority items first
        budget_limit = Decimal(str(budget.amount))
        if total_cost > budget_limit:
            # sort low->high priority and remove until within budget
            priority_order = {"low": 0, "medium": 1, "high": 2}
            sanitized_items.sort(key=lambda x: priority_order.get(x["priority"], 1))
            new_items = []
            running = Decimal(0)
            for it in sanitized_items:
                if running + it["estimated_price"] <= budget_limit:
                    new_items.append(it)
                    running += it["estimated_price"]
                # else skip
            sanitized_items = new_items
            total_cost = running

        # 6) Persist ShoppingList + Items atomically
        with transaction.atomic():
            sl = ShoppingList.objects.create(
                user=user,
                name=ai_json.get("list_name", "AI Smart Shopping List"),
                status="generated",
                budget_limit=budget.amount,
                total_estimated_cost=total_cost,
                total_actual_cost=None,
                pantry_utilization=0.0,  # will compute below
                goal_alignment=0.0,
                waste_reduction_score=0.0,
                week_number=timezone.now().isocalendar()[1],
                month=timezone.now().month,
                year=timezone.now().year,
            )

            # helper to get or create Ingredient safely
            def get_or_create_ingredient_safe(name, unit="g"):
                name_clean = name.strip()
                ing = Ingredient.objects.filter(name__iexact=name_clean).first()
                if ing:
                    return ing
                # create with required defaults
                return Ingredient.objects.create(
                    name=name_clean,
                    category="other",
                    barcode=None,
                    typical_expiry_days=None,
                    storage_instructions="",
                    calories=0.0,
                    protein=0.0,
                    carbs=0.0,
                    fat=0.0,
                    fiber=0.0,
                    common_units=unit,
                )

            # create items and compute pantry utilization score portions
            matched_count = 0
            uses_expiring_count = 0
            for it in sanitized_items:
                ing_obj = get_or_create_ingredient_safe(it["ingredient"], unit=it["unit"])
                ShoppingListItem.objects.create(
                    shopping_list=sl,
                    ingredient=ing_obj,
                    quantity=it["quantity"],
                    unit=it["unit"],
                    estimated_price=it["estimated_price"],
                    priority=it["priority"],
                    notes=it["reason"],
                    reason=it["reason"],
                )
                # check if pantry has this item (name match)
                if any(p['name'].lower() == ing_obj.name.lower() for p in pantry_items):
                    matched_count += 1
                if ing_obj.name.lower() in expiring_items:
                    uses_expiring_count += 1

            total_items = len(sanitized_items) or 1
            pantry_utilization = (matched_count / total_items) * 100
            # waste_reduction_score: percent of items that help use expiring items (simple heuristic)
            waste_reduction_score = (uses_expiring_count / total_items) * 100

            # Set basic goal alignment: if goal exists, mark 100% for now (can be improved)
            goal_alignment = 100.0 if goal else 0.0

            sl.pantry_utilization = round(pantry_utilization, 2)
            sl.waste_reduction_score = round(waste_reduction_score, 2)
            sl.goal_alignment = round(goal_alignment, 2)
            sl.save()

        return sl

    except Exception as e:
        print(f"Error generating AI shopping list: {e}")
        return None
