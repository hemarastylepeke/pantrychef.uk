from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserProfile, UserGoal, Budget
from .forms import UserProfileForm, DietaryRequirementsForm, UserGoalForm, BudgetForm, PreferencesForm
from django.http import JsonResponse

@login_required(login_url='account_login')
def profile_page_view(request):
    """
    Comprehensive profile page showing all user information and management options
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get related data
    goals = UserGoal.objects.filter(user=request.user, active=True)
    current_budget = Budget.objects.filter(user=request.user, active=True).first()
    budget_history = Budget.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Handle profile form submission
    profile_form = UserProfileForm(instance=profile)
    dietary_form = DietaryRequirementsForm(instance=profile)
    goal_form = UserGoalForm()
    budget_form = BudgetForm(instance=current_budget) if current_budget else BudgetForm()
    preferences_form = PreferencesForm(instance=profile)
    
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the profile form.')
                
        elif form_type == 'dietary':
            dietary_form = DietaryRequirementsForm(request.POST, instance=profile)
            if dietary_form.is_valid():
                dietary_form.save()
                messages.success(request, 'Dietary requirements updated successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the dietary requirements form.')
                
        elif form_type == 'goal':
            goal_form = UserGoalForm(request.POST)
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.user = request.user
                goal.save()
                messages.success(request, 'Goal added successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the goal form.')
                
        elif form_type == 'budget':
            # Deactivate current budget if exists
            if current_budget:
                current_budget.active = False
                current_budget.save()
                
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                budget = budget_form.save(commit=False)
                budget.user = request.user
                budget.active = True
                budget.save()
                messages.success(request, 'Budget set successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the budget form.')
                
        elif form_type == 'preferences':
            preferences_form = PreferencesForm(request.POST, instance=profile)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Preferences updated successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the preferences form.')
    
    # Prepare dietary data for template
    dietary_data = {
        'allergies': profile.allergies or [],
        'restrictions': profile.dietary_restrictions or [],
        'disliked_ingredients': profile.disliked_ingredients or [],
        'preferred_cuisines': profile.preferred_cuisines or []
    }
    
    context = {
        'profile': profile,
        'goals': goals,
        'current_budget': current_budget,
        'budget_history': budget_history,
        'dietary_data': dietary_data,
        
        # Forms
        'profile_form': profile_form,
        'dietary_form': dietary_form,
        'goal_form': goal_form,
        'budget_form': budget_form,
        'preferences_form': preferences_form,
    }
    
    return render(request, 'account/profile.html', context)

@login_required(login_url='account_login')
def edit_goal_view(request, goal_id):
    """
    Edit a specific goal
    """
    goal = get_object_or_404(UserGoal, id=goal_id, user=request.user)
    
    if request.method == 'POST':
        form = UserGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated successfully!')
            return redirect('profile_page')
        else:
            messages.error(request, 'Please correct the errors in the goal form.')
    else:
        form = UserGoalForm(instance=goal)
    
    context = {
        'form': form,
        'goal': goal,
        'editing': True
    }
    return render(request, 'account/edit_goal.html', context)

@login_required(login_url='account_login')
def delete_goal_view(request, goal_id):
    """
    Delete a goal (soft delete by setting active=False)
    """
    goal = get_object_or_404(UserGoal, id=goal_id, user=request.user)
    
    if request.method == 'POST':
        goal.active = False
        goal.save()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('profile_page')
    
    context = {
        'goal': goal
    }
    return render(request, 'account/delete_goal.html', context)

@login_required(login_url='account_login')
def update_goal_progress_ajax(request, goal_id):
    """
    AJAX view to update goal progress without page reload
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        goal = get_object_or_404(UserGoal, id=goal_id, user=request.user)
        current_value = request.POST.get('current_value')
        
        try:
            goal.current_value = float(current_value)
            goal.save()
            
            # Calculate progress percentage
            progress = 0
            if goal.target_value and goal.target_value > 0:
                progress = min(100, (goal.current_value / goal.target_value) * 100)
            
            return JsonResponse({
                'success': True,
                'current_value': goal.current_value,
                'progress': round(progress, 1),
                'goal_type': goal.get_goal_type_display()
            })
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid value provided'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required(login_url='account_login')
def quick_budget_update_ajax(request):
    """
    AJAX view for quick budget updates
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        budget = Budget.objects.filter(user=request.user, active=True).first()
        if budget:
            amount = request.POST.get('amount')
            try:
                budget.amount = float(amount)
                budget.save()
                return JsonResponse({
                    'success': True, 
                    'new_amount': budget.amount,
                    'currency': budget.currency,
                    'period': budget.get_period_display()
                })
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid amount provided'})
        
        return JsonResponse({'success': False, 'error': 'No active budget found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})