from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import UserPantry, Ingredient, Recipe, Budget, ShoppingList, ShoppingListItem, FoodWasteRecord
from django.db.models import Sum
from .forms import PantryItemForm, IngredientForm, BudgetForm, ShoppingListForm, ShoppingListItemForm, RecipeForm
from django.db.models import Q
from django.forms import formset_factory
from core.services.recipe_suggestion_ai import generate_ai_recipe_from_openai
from core.services.ai_shopping_service import generate_ai_shopping_list, confirm_shopping_list, detect_and_record_food_waste
from decimal import Decimal
from django.db import transaction



#-------------------------------------------------------PANTRY MANAGEMENT VIEWS------------------------------------------------------------------#
# Pantry list item
@login_required(login_url='account_login')
def pantry_list_view(request):
    """
    list of all pantry
    """
    pantry_items = UserPantry.objects.filter(user=request.user).order_by('expiry_date')
    
    context = {
        'pantry_items': pantry_items,
    }
    return render(request, 'core/pantry_list.html', context)


# Add pantry item view
@login_required(login_url='account_login')
def add_pantry_item_view(request):
    """
    Add new item to pantry via form
    """
    if request.method == 'POST':
        form = PantryItemForm(request.POST, request.FILES)
        if form.is_valid():
            pantry_item = form.save(commit=False)
            pantry_item.user = request.user
            
            # Handle image uploads
            if 'product_image' in request.FILES:
                pantry_item.product_image = request.FILES['product_image']
            if 'expiry_label_image' in request.FILES:
                pantry_item.expiry_label_image = request.FILES['expiry_label_image']
            
            pantry_item.save()
            messages.success(request, f'{pantry_item.ingredient.name} added to pantry!')
            return redirect('pantry_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PantryItemForm()
    
    context = {
        'form': form,
        'ingredients': Ingredient.objects.all().order_by('name')
    }
    return render(request, 'core/add_pantry_item.html', context)

# Edit pantry item view
@login_required(login_url='account_login')
def edit_pantry_item_view(request, item_id):
    """
    Edit existing pantry item
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = PantryItemForm(request.POST, request.FILES, instance=pantry_item)
        if form.is_valid():
            form.save()
            messages.success(request, f'{pantry_item.ingredient.name} updated successfully!')
            return redirect('pantry_list')
    else:
        form = PantryItemForm(instance=pantry_item)
    
    context = {
        'form': form,
        'pantry_item': pantry_item
    }
    return render(request, 'core/edit_pantry_item.html', context)

# Delete pantry item view
@login_required(login_url='account_login')
def delete_pantry_item_view(request, item_id):
    """
    Delete pantry item
    """
    pantry_item = get_object_or_404(UserPantry, id=item_id, user=request.user)
    
    if request.method == 'POST':
        pantry_item.delete()
        messages.success(request, f'{pantry_item.ingredient.name} deleted successfully!')
        return redirect('pantry_list')
    
    context = {
        'pantry_item': pantry_item
    }
    return render(request, 'core/delete_pantry_item.html', context)


#----------------------------------------------------------INGREDIENT VIEWS----------------------------------------------------------------------------#
# Ingredient List View
@login_required(login_url='account_login')
def ingredient_list_view(request):
    """
    List all ingredients that belongs to a user
    """
    ingredients = Ingredient.objects.order_by('name')

    context = {
        'ingredients': ingredients,
    }
    return render(request, 'core/ingredient_list.html', context)

# Add Ingredient View
@login_required(login_url='account_login')
def add_ingredient_view(request):
    """
    Add new ingredient to the database
    """
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save()
            messages.success(request, f'Ingredient "{ingredient.name}" added successfully!')
            return redirect('ingredient_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IngredientForm()
    
    context = {
        'form': form,
        'title': 'Add New Ingredient'
    }
    return render(request, 'core/ingredient_form.html', context)

# Edit Ingredient View
@login_required(login_url='account_login')
def edit_ingredient_view(request, ingredient_id):
    """
    Edit existing ingredient
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            updated_ingredient = form.save()
            messages.success(request, f'Ingredient "{updated_ingredient.name}" updated successfully!')
            return redirect('ingredient_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IngredientForm(instance=ingredient)
    
    context = {
        'form': form,
        'ingredient': ingredient,
        'title': f'Edit {ingredient.name}'
    }
    return render(request, 'core/ingredient_form.html', context)

# Delete Ingredient View
@login_required(login_url='account_login')
def delete_ingredient_view(request, ingredient_id):
    """
    Delete ingredient from database
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        ingredient_name = ingredient.name
        ingredient.delete()
        messages.success(request, f'Ingredient "{ingredient_name}" deleted successfully!')
        return redirect('ingredient_list')
    
    context = {
        'ingredient': ingredient
    }
    return render(request, 'core/delete_ingredient.html', context)

# Ingredient Detail View
@login_required(login_url='account_login')
def ingredient_detail_view(request, ingredient_id):
    """
    View ingredient details
    """
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    # Get pantry items that use this ingredient
    pantry_items = UserPantry.objects.filter(ingredient=ingredient)[:10]
    
    context = {
        'ingredient': ingredient,
        'pantry_items': pantry_items,
    }
    return render(request, 'core/ingredient_detail.html', context)

#-----------------------------------------------------BUDGET MANAGEMENT VIEWS-------------------------------------------------------------------------#
# Budget List View
@login_required(login_url='account_login')
def budget_list_view(request):
    """
    List all budgets for the user
    """
    budgets = Budget.objects.filter(user=request.user).order_by('-start_date')
    
    # Calculate some statistics
    active_budget = budgets.filter(active=True).first()
    total_budgets = budgets.count()
    total_amount_allocated = sum(budget.amount for budget in budgets)
    total_amount_spent = sum(budget.amount_spent for budget in budgets)
    
    context = {
        'budgets': budgets,
        'active_budget': active_budget,
        'total_budgets': total_budgets,
        'total_amount_allocated': total_amount_allocated,
        'total_amount_spent': total_amount_spent,
    }
    return render(request, 'core/budget_list.html', context)

# Budget Detail View
@login_required(login_url='account_login')
def budget_detail_view(request, budget_id):
    """
    View budget details and spending analysis
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    # Calculate spending statistics using Budget model methods
    spending_percentage = budget.get_spending_percentage()
    days_remaining = (budget.end_date - timezone.now().date()).days if budget.end_date else 0
    daily_budget = budget.get_remaining_budget() / max(days_remaining, 1) if days_remaining > 0 else 0
    
    # Get confirmed shopping lists using Budget model method
    confirmed_shopping_lists = budget.get_confirmed_shopping_lists()
    
    # Get spending breakdown by category
    spending_breakdown = budget.get_spending_breakdown()
    
    # Weekly spending breakdown
    weekly_spending = []
    if budget.period == 'weekly':
        current_date = budget.start_date
        week_count = 1
        while current_date <= (budget.end_date or timezone.now().date()):
            week_end = min(current_date + timedelta(days=6), budget.end_date or timezone.now().date())
            
            week_spending = ShoppingList.objects.filter(
                user=request.user,
                status='confirmed',
                completed_at__date__gte=current_date,
                completed_at__date__lte=week_end
            ).aggregate(total=Sum('total_actual_cost'))['total'] or Decimal('0.00')
            
            weekly_spending.append({
                'week': f"Week {week_count}",
                'period': f"{current_date.strftime('%b %d')} - {week_end.strftime('%b %d')}",
                'amount': week_spending
            })
            
            current_date = week_end + timedelta(days=1)
            week_count += 1
    
    context = {
        'budget': budget,
        'spending_percentage': min(spending_percentage, 100),
        'days_remaining': max(days_remaining, 0),
        'daily_budget': daily_budget,
        'confirmed_shopping_lists': confirmed_shopping_lists[:10],
        'total_from_shopping_lists': budget.get_total_spent_from_shopping_lists(),
        'spending_breakdown': spending_breakdown,
        'remaining_budget': budget.get_remaining_budget(),
        'weekly_spending': weekly_spending,
    }
    return render(request, 'core/budget_detail.html', context)

# Create Budget View
@login_required(login_url='account_login')
def create_budget_view(request):
    """
    Create a new budget
    """
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            
            # Set end date based on period
            if budget.period == 'weekly':
                budget.end_date = budget.start_date + timedelta(days=7)
            elif budget.period == 'monthly':
                budget.end_date = budget.start_date + timedelta(days=30)
            
            budget.save()
            messages.success(request, f'Budget created successfully!')
            return redirect('budget_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Set default start date to today
        form = BudgetForm(initial={'start_date': timezone.now().date()})
    
    context = {
        'form': form,
        'title': 'Create New Budget'
    }
    return render(request, 'core/budget_form.html', context)

# Edit Budget View
@login_required(login_url='account_login')
def edit_budget_view(request, budget_id):
    """
    Edit existing budget
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            updated_budget = form.save(commit=False)
            
            # Update end date if period changed
            if 'period' in form.changed_data or 'start_date' in form.changed_data:
                if updated_budget.period == 'weekly':
                    updated_budget.end_date = updated_budget.start_date + timedelta(days=7)
                elif updated_budget.period == 'monthly':
                    updated_budget.end_date = updated_budget.start_date + timedelta(days=30)
            
            updated_budget.save()
            messages.success(request, f'Budget updated successfully!')
            return redirect('budget_detail', budget_id=budget.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BudgetForm(instance=budget)
    
    context = {
        'form': form,
        'budget': budget,
        'title': f'Edit Budget'
    }
    return render(request, 'core/budget_form.html', context)

# Delete Budget View
@login_required(login_url='account_login')
def delete_budget_view(request, budget_id):
    """
    Delete budget
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        budget_name = f"{budget.amount} {budget.currency}/{budget.period}"
        budget.delete()
        messages.success(request, f'Budget "{budget_name}" deleted successfully!')
        return redirect('core:budget_list')
    
    context = {
        'budget': budget
    }
    return render(request, 'core/delete_budget.html', context)

# Toggle Budget Active Status
@login_required(login_url='account_login')
def toggle_budget_active_view(request, budget_id):
    """
    Toggle budget active status
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        # Deactivate all other budgets
        if not budget.active:
            Budget.objects.filter(user=request.user, active=True).update(active=False)
        
        budget.active = not budget.active
        budget.save()
        
        status = "activated" if budget.active else "deactivated"
        messages.success(request, f'Budget {status} successfully!')
    
    return redirect('budget_list')

# Budget Analytics View
# Should be able to track the amount of money spent everytime a user confirms a shopping list
@login_required(login_url='account_login')
def budget_analytics_view(request):
    """
    Show budget analytics and spending trends
    """
    budgets = Budget.objects.filter(user=request.user).order_by('start_date')
    
    # Calculate monthly spending trends
    monthly_spending = []
    now = timezone.now().date()  # Use date instead of datetime

    for i in range(6):  # Last 6 months
        month_start = (now.replace(day=1) - timedelta(days=30*i))
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_budget = sum(
            budget.amount_spent for budget in budgets 
            if budget.start_date and budget.end_date and 
            budget.start_date <= month_end and budget.end_date >= month_start
        )
        
        monthly_spending.append({
            'month': month_start.strftime('%b %Y'),
            'amount': monthly_budget
        })
    
    monthly_spending.reverse()
    
    context = {
        'budgets': budgets,
        'monthly_spending': monthly_spending,
        'total_budgets': budgets.count(),
        'total_allocated': sum(budget.amount for budget in budgets),
        'total_spent': sum(budget.amount_spent for budget in budgets),
    }
    return render(request, 'core/budget_analytics.html', context)


#-----------------------------------------------------SHOPPING LIST VIEWS-------------------------------------------------------------------------#
# Shopping List List View
@login_required(login_url='account_login')
def shopping_list_list_view(request):
    """
    List all shopping lists for the user
    """
    shopping_lists = ShoppingList.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_lists = shopping_lists.count()
    completed_lists = shopping_lists.filter(status='completed').count()
    total_estimated_cost = shopping_lists.aggregate(total=Sum('total_estimated_cost'))['total'] or 0
    total_actual_cost = shopping_lists.aggregate(total=Sum('total_actual_cost'))['total'] or 0
    
    # Get recent lists (last 5)
    recent_lists = shopping_lists[:5]
    
    context = {
        'shopping_lists': shopping_lists,
        'recent_lists': recent_lists,
        'total_lists': total_lists,
        'completed_lists': completed_lists,
        'total_estimated_cost': total_estimated_cost,
        'total_actual_cost': total_actual_cost,
    }
    return render(request, 'core/shopping_list_list.html', context)

@login_required(login_url='account_login')
def create_shopping_list_view(request):
    """
    Create an AI-powered shopping list.
    - Uses the active user budget (weekly/monthly).
    - Generates a draft list with estimated costs and missing ingredients.
    - Tracks estimated spending (later compared to actual confirmed spend).
    """

    if request.method == "POST":
        # user can optionally specify a target budget period
        period = request.POST.get("period") or "weekly"

        # validate user has an active budget
        budget = Budget.objects.filter(user=request.user, active=True).order_by('-start_date').first()
        if not budget:
            messages.error(request, "Please set an active budget before generating a shopping list.")
            return redirect('budget_setup')

        messages.info(request, "Generating AI-powered shopping list... Please wait a moment.")

        # call the AI generator
        ai_list = generate_ai_shopping_list(request.user)

        if ai_list:
            ai_list.status = "generated"
            ai_list.period = period
            ai_list.generated_at = timezone.now()
            ai_list.save()

            messages.success(
                request,
                f'AI-generated shopping list "{ai_list.name}" created successfully within your budget of '
                f'{budget.amount} {budget.currency}. '
                f'Estimated total cost: {ai_list.total_estimated_cost}. '
                f'Please review and confirm purchases after shopping.'
            )
            return redirect('shopping_list_detail', list_id=ai_list.id)
        else:
            messages.error(request, "AI failed to generate a shopping list. Please try again later.")
            return redirect('shopping_list_list')

    #
    active_budget = Budget.objects.filter(user=request.user, active=True).order_by('-start_date').first()
    if not active_budget:
        messages.warning(request, "You need to set an active budget before creating an AI shopping list.")
        return redirect('budget_setup')

    context = {
        "title": "AI Smart Shopping List",
        "active_budget": active_budget,
    }
    return render(request, "core/ai_shopping_list_setup.html", context)

# Edit Shopping List View
@login_required(login_url='account_login')
def edit_shopping_list_view(request, list_id):
    """
    Edit existing shopping list and its items
    """
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    ShoppingListItemFormSet = formset_factory(ShoppingListItemForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        form = ShoppingListForm(request.POST, instance=shopping_list)
        formset = ShoppingListItemFormSet(request.POST, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            # Update shopping list
            updated_list = form.save(commit=False)
            
            # Calculate new total estimated cost
            total_estimated_cost = 0
            items_to_save = []
            
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    if hasattr(item, 'shopping_list'):
                        item.shopping_list = updated_list
                    else:
                        item.shopping_list_id = updated_list.id
                    if item.estimated_price:
                        total_estimated_cost += item.estimated_price
                    items_to_save.append(item)
            
            # Save everything
            updated_list.total_estimated_cost = total_estimated_cost
            updated_list.save()
            
            # Delete existing items and save new ones
            shopping_list.items.all().delete()
            for item in items_to_save:
                item.save()
            
            messages.success(request, f'Shopping list "{updated_list.name}" updated successfully!')
            return redirect('shopping_list_detail', list_id=updated_list.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ShoppingListForm(instance=shopping_list)
        
        # Initialize formset with existing items
        initial_data = []
        for item in shopping_list.items.all():
            initial_data.append({
                'ingredient': item.ingredient,
                'quantity': item.quantity,
                'unit': item.unit,
                'estimated_price': item.estimated_price,
                'priority': item.priority,
                'notes': item.notes,
                'reason': item.reason,
            })
        
        formset = ShoppingListItemFormSet(initial=initial_data, prefix='items')
    
    context = {
        'form': form,
        'formset': formset,
        'shopping_list': shopping_list,
        'title': f'Edit {shopping_list.name}'
    }
    return render(request, 'core/shopping_list_form.html', context)


# Delete Shopping List View
@login_required(login_url='account_login')
def delete_shopping_list_view(request, list_id):
    """
    Delete shopping list
    """
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    
    if request.method == 'POST':
        list_name = shopping_list.name
        shopping_list.delete()
        messages.success(request, f'Shopping list "{list_name}" deleted successfully!')
        return redirect('core:shopping_list_list')
    
    context = {
        'shopping_list': shopping_list
    }
    return render(request, 'core/delete_shopping_list.html', context)


# Shopping List Detail View
@login_required(login_url='account_login')
def shopping_list_detail_view(request, list_id):
    """
    View shopping list details and allow the user to confirm purchases.
    Confirmation records actual price/quantity/expiry and updates pantry via service.
    After confirmation, updates budget spending and triggers food waste detection.
    """
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    items_qs = shopping_list.items.select_related('ingredient').order_by('-priority', 'ingredient__name')

    # Group by priority for display
    high_priority_items = items_qs.filter(priority='high')
    medium_priority_items = items_qs.filter(priority='medium')
    low_priority_items = items_qs.filter(priority='low')

    total_items = items_qs.count()
    purchased_items = items_qs.filter(purchased=True).count()
    purchased_percentage = (purchased_items / total_items * 100) if total_items > 0 else 0

    total_estimated = items_qs.aggregate(total=Sum('estimated_price'))['total'] or Decimal('0.00')
    total_actual = items_qs.aggregate(total=Sum('actual_price'))['total'] or Decimal('0.00')

    # Handle confirmation POST
    if request.method == "POST" and request.POST.get("action") == "confirm":
        purchased_payload = []
        total_actual_cost = Decimal('0.00')
        
        # Collect all purchased items and calculate total cost
        for sli in items_qs:
            prefix_id = str(sli.id)
            purchased_flag = request.POST.get(f"purchased_{prefix_id}") == "on"
            if purchased_flag:
                actual_price_raw = request.POST.get(f"actual_price_{prefix_id}")
                qty_raw = request.POST.get(f"purchased_qty_{prefix_id}")
                expiry_date_raw = request.POST.get(f"expiry_date_{prefix_id}")
                expiry_file = request.FILES.get(f"expiry_image_{prefix_id}")

                # Calculate actual price for this item
                actual_price = Decimal(actual_price_raw) if actual_price_raw and actual_price_raw.strip() else sli.estimated_price
                total_actual_cost += actual_price

                item_payload = {
                    "shopping_list_item_id": sli.id,
                    "actual_price": float(actual_price) if actual_price else None,
                    "purchased_quantity": float(qty_raw) if qty_raw and qty_raw.strip() else sli.quantity,
                    "expiry_date": expiry_date_raw if expiry_date_raw and expiry_date_raw.strip() else None,
                    "expiry_label_image": expiry_file,
                }
                purchased_payload.append(item_payload)

        # Use form total if provided, otherwise use calculated total
        total_actual_cost_raw = request.POST.get("total_actual_cost")
        if total_actual_cost_raw and total_actual_cost_raw.strip():
            try:
                total_actual_cost = Decimal(total_actual_cost_raw)
            except (decimal.InvalidOperation, ValueError):
                # If invalid decimal, keep the calculated total
                pass

        # Validate that at least one item was purchased
        if not purchased_payload:
            messages.error(request, "Please select at least one item to confirm as purchased.")
            # STAY ON THE SAME PAGE instead of redirecting
            # This allows the user to see the error and select items
            pass  # Continue to render the template with error message
        else:
            try:
                # Step 1: confirm purchases via service within transaction
                with transaction.atomic():
                    result = confirm_shopping_list(
                        request.user,
                        shopping_list.id,
                        purchased_payload,
                        total_actual_cost=float(total_actual_cost)
                    )

                    if result:
                        # Update budget spending
                        today = timezone.now().date()
                        active_budget = Budget.objects.filter(
                            user=request.user,
                            active=True,
                            start_date__lte=today,
                            end_date__gte=today
                        ).first()
                        
                        if active_budget:
                            # Use the sync_amount_spent method to ensure data consistency
                            new_total_spent = active_budget.sync_amount_spent()
                            
                            messages.success(request, 
                                f'Shopping list confirmed successfully! ${total_actual_cost} spent. '
                                f'Budget updated: ${new_total_spent} spent of ${active_budget.amount}. '
                                f'Remaining budget: ${active_budget.get_remaining_budget()}'
                            )
                        else:
                            messages.success(request, 
                                f'Shopping list confirmed successfully! ${total_actual_cost} spent. '
                                'No active budget found for tracking.'
                            )
                        
                        # Step 3: Detect food waste after confirmation
                        try:
                            waste_detected = detect_and_record_food_waste(request.user)
                            if waste_detected:
                                messages.info(request, "Food waste analysis completed. Check your analytics for details.")
                        except Exception as waste_error:
                            messages.warning(request, f"Purchases confirmed, but food waste analysis encountered an issue: {str(waste_error)}")
                        
                        # Redirect to shopping list only if successful
                        return redirect('shopping_lists')
                    
                    else:
                        messages.error(request, "Failed to confirm purchases. Please try again.")
                        
            except Exception as e:
                messages.error(request, f"Error confirming purchases: {str(e)}")

    # show list detail with enhanced context
    today = timezone.now().date()
    active_budget = Budget.objects.filter(
        user=request.user,
        active=True,
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    # Calculate budget information for display
    budget_info = None
    if active_budget:
        budget_info = {
            'budget': active_budget,
            'remaining': active_budget.get_remaining_budget(),
            'spent_percentage': active_budget.get_spending_percentage(),
            'daily_budget': active_budget.get_remaining_budget() / max((active_budget.end_date - today).days, 1) if active_budget.end_date else Decimal('0.00')
        }

    # Get items that need expiry dates
    items_needing_expiry = items_qs.filter(
        ingredient__typical_expiry_days__isnull=False
    ).exclude(ingredient__typical_expiry_days=0)

    context = {
        'shopping_list': shopping_list,
        'high_priority_items': high_priority_items,
        'medium_priority_items': medium_priority_items,
        'low_priority_items': low_priority_items,
        'total_items': total_items,
        'purchased_items': purchased_items,
        'purchased_percentage': purchased_percentage,
        'total_estimated': total_estimated,
        'total_actual': total_actual,
        'active_budget': active_budget,
        'budget_info': budget_info,
        'items_needing_expiry': items_needing_expiry,
        'today': today,
    }
    return render(request, 'core/shopping_list_detail.html', context)

#--------------------------------------------------RECIPE MANAGEMENT VIEWS-------------------------------------------------------------------------#
# Recipe List View
@login_required(login_url='account_login')
def recipe_list_view(request):
    """
    List all recipes with filtering and search
    """
    recipes = Recipe.objects.all().order_by('-created_at')
    
    # Filtering
    cuisine_filter = request.GET.get('cuisine', '')
    difficulty_filter = request.GET.get('difficulty', '')
    search_query = request.GET.get('search', '')
    
    if cuisine_filter:
        recipes = recipes.filter(cuisine=cuisine_filter)
    
    if difficulty_filter:
        recipes = recipes.filter(difficulty=difficulty_filter)
    
    if search_query:
        recipes = recipes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ingredients__icontains=search_query) |
            Q(dietary_tags__icontains=search_query)
        )
    
    # Statistics
    total_recipes = recipes.count()
    user_recipes = recipes.filter(created_by=request.user).count()
    ai_recipes = recipes.filter(is_ai_generated=True).count()
    
    context = {
        'recipes': recipes,
        'cuisine_filter': cuisine_filter,
        'difficulty_filter': difficulty_filter,
        'search_query': search_query,
        'total_recipes': total_recipes,
        'user_recipes': user_recipes,
        'ai_recipes': ai_recipes,
    }
    return render(request, 'core/recipe_list.html', context)

@login_required(login_url='account_login')
def recipe_detail_view(request, recipe_id):
    """
    View recipe details
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Get ingredients properly (ManyToMany)
    ingredients_list = recipe.ingredients.all()

    # Parse instructions into steps (still fine since it's text)
    instructions_list = []
    if recipe.instructions:
        instructions_list = [line.strip() for line in recipe.instructions.split('\n') if line.strip()]

    # Handle prep_time and cook_time safely
    total_time = (recipe.prep_time or 0) + (recipe.cook_time or 0)

    # Get similar recipes
    similar_recipes = Recipe.objects.filter(
        cuisine=recipe.cuisine
    ).exclude(id=recipe.id).order_by('?')[:4]

    context = {
        'recipe': recipe,
        'ingredients_list': ingredients_list,
        'instructions_list': instructions_list,
        'total_time': total_time,
        'similar_recipes': similar_recipes,
    }

    return render(request, 'core/recipe_detail.html', context)

# Create Recipe View
@login_required(login_url='account_login')
def create_recipe_view(request):
    """
    Generate a new recipe using AI based on:
    - User profile (goal, allergies, budget)
    - Available pantry ingredients
    - Expiring items to reduce food waste

    Replaces manual recipe creation.
    """
    if request.method == 'POST':
        try:
            # Call the AI service to generate and save a recipe
            recipe = generate_ai_recipe_from_openai(request.user)
            messages.success(request, f'AI Recipe "{recipe.name}" generated successfully!')
            return redirect('recipe_detail', recipe_id=recipe.id)
        except Exception as e:
            messages.error(request, f"Error generating AI recipe: {str(e)}")
            return redirect('create_recipe')
    
    context = {
        'title': 'Generate AI Recipe',
    }
    return render(request, 'core/ai_generate_recipe.html', context)


# Edit Recipe View
@login_required(login_url='account_login')
def edit_recipe_view(request, recipe_id):
    """
    Edit existing recipe
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Check if user owns the recipe or is superuser
    if recipe.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this recipe.')
        return redirect('recipe_detail', recipe_id=recipe.id)
    
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            updated_recipe = form.save()
            
            # Handle image upload
            if 'image' in request.FILES:
                updated_recipe.image = request.FILES['image']
            
            updated_recipe.save()
            messages.success(request, f'Recipe "{updated_recipe.name}" updated successfully!')
            return redirect('recipe_detail', recipe_id=updated_recipe.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecipeForm(instance=recipe)
    
    context = {
        'form': form,
        'recipe': recipe,
        'title': f'Edit {recipe.name}'
    }
    return render(request, 'core/recipe_form.html', context)

# Delete Recipe View
@login_required(login_url='account_login')
def delete_recipe_view(request, recipe_id):
    """
    Delete recipe
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Check if user owns the recipe or is superuser
    if recipe.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this recipe.')
        return redirect('recipe_list')
    
    if request.method == 'POST':
        recipe_name = recipe.name
        recipe.delete()
        messages.success(request, f'Recipe "{recipe_name}" deleted successfully!')
        return redirect('core:recipe_list')
    
    context = {
        'recipe': recipe
    }
    return render(request, 'core/delete_recipe.html', context)

# My Recipes View
@login_required(login_url='account_login')
def my_recipes_view(request):
    """
    View recipes created by the current user
    """
    recipes = Recipe.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'recipes': recipes,
        'total_recipes': recipes.count(),
    }
    return render(request, 'core/my_recipes.html', context)

# Food Waste Analytics View
def food_waste_analytics_view(request):
    """
    Display user's food waste analytics after shopping list confirmation.
    """
    user = request.user
    waste_records = FoodWasteRecord.objects.filter(user=user)

    total_wasted_cost = waste_records.aggregate(Sum('cost'))['cost__sum'] or 0
    total_wasted_qty = waste_records.aggregate(Sum('quantity_wasted'))['quantity_wasted__sum'] or 0

    by_reason = (
        waste_records.values('reason')
        .annotate(total=Sum('quantity_wasted'))
        .order_by('-total')
    )

    context = {
        "total_wasted_cost": total_wasted_cost,
        "total_wasted_qty": total_wasted_qty,
        "waste_by_reason": by_reason,
        "waste_records": waste_records,
    }

    return render(request, "core/food_waste_analytics.html", context)

   