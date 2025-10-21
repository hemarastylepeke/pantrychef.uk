from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import UserPantry, Ingredient, Recipe, Budget
from .forms import PantryItemForm, IngredientForm, BudgetForm
from .services.vision_service import ExpiryDateDetector

# Helper functions
def calculate_waste_savings(user):
    """Calculate total waste savings for the user"""
    # Implement your logic here
    return 156  # Example value

def get_recipe_suggestions(user):
    """Get AI-powered recipe suggestions based on pantry items"""
    # Implement your logic here
    return [
        {
            'name': 'Veggie Omelette',
            'matching_ingredients': ['eggs', 'spinach', 'tomatoes'],
            'match_percentage': 95,
            'prep_time': 15,
            'calories': 320,
            'rating': 4.5
        },
        {
            'name': 'Pasta Pomodoro', 
            'matching_ingredients': ['pasta', 'tomatoes', 'basil'],
            'match_percentage': 88,
            'prep_time': 25,
            'calories': 450,
            'rating': 4.2
        }
    ]

# Pantry Management Views
@login_required(login_url='account_login')
def pantry_dashboard_view(request):
    """
    Main pantry dashboard showing current inventory and alerts
    """
    # Get user's pantry items
    pantry_items = UserPantry.objects.filter(user=request.user, status='active').order_by('expiry_date')
    
    # Get items expiring soon (within 3 days)
    soon = timezone.now().date() + timedelta(days=3)
    expiring_soon = pantry_items.filter(expiry_date__lte=soon)
    
    # Add days until expiry for template
    for item in expiring_soon:
        item.days_until_expiry = (item.expiry_date - timezone.now().date()).days
    
    # Get recently expired items
    expired_items = pantry_items.filter(expiry_date__lt=timezone.now().date())
    
    # Calculate pantry statistics
    total_items = pantry_items.count()
    total_value = sum(item.price for item in pantry_items if item.price)
    
    # Calculate waste savings
    waste_savings = calculate_waste_savings(request.user)
    
    # Recipe suggestions
    recipe_suggestions = get_recipe_suggestions(request.user)
    
    # Waste reduction tips
    waste_tips = [
        "Freeze leftover bread to use for croutons or breadcrumbs.",
        "Use vegetable scraps to make homemade broth.",
        "Plan meals around ingredients that will expire soon.",
        "Store herbs in water to keep them fresh longer.",
        "Use overripe fruits in smoothies or baking."
    ]
    
    # Budget information
    current_budget = Budget.objects.filter(user=request.user, active=True).first()
    budget_percentage = 0
    if current_budget:
        budget_percentage = min(100, int((current_budget.amount_spent / current_budget.amount) * 100))
    
    context = {
        'pantry_items': pantry_items,
        'expiring_soon': expiring_soon,
        'expired_items': expired_items,
        'total_items': total_items,
        'total_value': total_value,
        'waste_savings': waste_savings,
        'waste_reduction_percentage': 24,
        'recipes_created': Recipe.objects.filter(created_by=request.user).count(),
        'pantry_utilization': 85,
        'current_budget': current_budget,
        'budget_percentage': budget_percentage,
        'recipe_suggestions': recipe_suggestions,
        'waste_tips': waste_tips,
        'pantry_form': PantryItemForm(),
    }
    return render(request, 'core/pantry_dashboard.html', context)


#-------------------------------------------------------PANTRY MANAGEMENT VIEWS---------------------------------------------------------------------------#
# Pantry list item
@login_required(login_url='account_login')
def pantry_list_view(request):
    """
    list of all pantry items
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
            return redirect('pantry_dashboard')
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
    List all ingredients with search functionality
    """
    ingredients = Ingredient.objects.all().order_by('name')

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
        return redirect('core:ingredient_list')
    
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
    
    # Calculate spending statistics
    spending_percentage = (budget.amount_spent / budget.amount * 100) if budget.amount > 0 else 0
    days_remaining = (budget.end_date - timezone.now().date()).days if budget.end_date else 0
    daily_budget = (budget.amount - budget.amount_spent) / max(days_remaining, 1) if days_remaining > 0 else 0
    
    # Get recent shopping lists for this budget period
    shopping_lists = ShoppingList.objects.filter(
        user=request.user,
        created_at__date__gte=budget.start_date,
        created_at__date__lte=budget.end_date if budget.end_date else timezone.now().date()
    ).order_by('-created_at')[:10]
    
    # Get pantry items purchased during budget period
    pantry_items = UserPantry.objects.filter(
        user=request.user,
        purchase_date__gte=budget.start_date,
        purchase_date__lte=budget.end_date if budget.end_date else timezone.now().date()
    ).exclude(price__isnull=True).order_by('-purchase_date')[:15]
    
    context = {
        'budget': budget,
        'spending_percentage': min(spending_percentage, 100),
        'days_remaining': max(days_remaining, 0),
        'daily_budget': daily_budget,
        'shopping_lists': shopping_lists,
        'pantry_items': pantry_items,
        'remaining_budget': budget.amount - budget.amount_spent,
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
            return redirect('core:budget_list')
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
            return redirect('core:budget_detail', budget_id=budget.id)
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
    
    return redirect('core:budget_list')

# Budget Analytics View
@login_required(login_url='account_login')
def budget_analytics_view(request):
    """
    Show budget analytics and spending trends
    """
    budgets = Budget.objects.filter(user=request.user).order_by('start_date')
    
    # Calculate monthly spending trends
    monthly_spending = []
    for i in range(6):  # Last 6 months
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
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