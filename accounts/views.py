from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserProfile, UserGoal
from .forms import (
    UserProfileForm, 
    DietaryRequirementsForm, 
    PreferencesForm, 
    CompleteUserProfileForm, 
    UserGoalFormSet, UserGoalForm
)

# Create profile view
@login_required(login_url='account_login')
def create_profile_view(request):
    """
    Allow a user to manually create a profile after account creation, including setting goals.
    """
    if UserProfile.objects.filter(user=request.user).exists():
        messages.info(request, 'You already have a profile.')
        return redirect('profile_page')

    if request.method == 'POST':
        profile_form = CompleteUserProfileForm(request.POST, request.FILES)
        goal_form = UserGoalForm(request.POST)  # no instance yet, new goal

        if profile_form.is_valid() and goal_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()

            # Save goal linked to profile
            goal = goal_form.save(commit=False)
            goal.user_profile = profile
            goal.save()

            messages.success(request, 'Your profile and goals were created successfully!')
            return redirect('profile_page')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = CompleteUserProfileForm()
        goal_form = UserGoalForm()

    context = {
        'form': profile_form,
        'goal_form': goal_form,
    }
    return render(request, 'account/create_profile.html', context)



# View and update profile
@login_required(login_url='account_login')
def profile_page_view(request):
    """Display and update user's profile and goals."""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Instantiate profile forms
    profile_form = UserProfileForm(instance=profile)
    dietary_form = DietaryRequirementsForm(instance=profile)
    preferences_form = PreferencesForm(instance=profile)

    # Goals formset
    goal_qs = UserGoal.objects.filter(user_profile=profile)
    goal_formset = UserGoalFormSet(queryset=goal_qs)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # Update profile info
        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile_page')
            messages.error(request, 'Please correct the errors in the profile form.')

        # Update dietary info
        elif form_type == 'dietary':
            dietary_form = DietaryRequirementsForm(request.POST, instance=profile)
            if dietary_form.is_valid():
                dietary_form.save()
                messages.success(request, 'Dietary requirements updated successfully!')
                return redirect('profile_page')
            messages.error(request, 'Please correct the errors in the dietary form.')

        # Update preferences
        elif form_type == 'preferences':
            preferences_form = PreferencesForm(request.POST, instance=profile)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Preferences updated successfully!')
                return redirect('profile_page')
            messages.error(request, 'Please correct the errors in the preferences form.')

        # Update or add goals
        elif form_type == 'goals':
            goal_formset = UserGoalFormSet(request.POST, queryset=goal_qs)
            if goal_formset.is_valid():
                instances = goal_formset.save(commit=False)
                for instance in instances:
                    instance.user_profile = profile
                    instance.save()
                for deleted in goal_formset.deleted_objects:
                    deleted.delete()
                messages.success(request, 'Goals updated successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in your goals.')

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'dietary_form': dietary_form,
        'preferences_form': preferences_form,
        'goal_formset': goal_formset,
    }
    return render(request, 'account/profile.html', context)


@login_required(login_url='account_login')
def edit_profile_view(request):
    """
    Edit profile view that handles all profile fields and user goals.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Get or create goal record linked to the profile
    user_goal, created = UserGoal.objects.get_or_create(user_profile=profile, active=True)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Personal information updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the personal information form.')

        elif form_type == 'dietary':
            profile.allergies = request.POST.get('allergies', '')
            profile.dietary_restrictions = request.POST.get('dietary_restrictions', '')
            profile.disliked_ingredients = request.POST.get('disliked_ingredients', '')
            profile.save()
            messages.success(request, 'Dietary requirements updated successfully!')
            return redirect('edit_profile')

        elif form_type == 'preferences':
            profile.preferred_cuisines = request.POST.get('preferred_cuisines', '')
            profile.save()
            messages.success(request, 'Preferences updated successfully!')
            return redirect('edit_profile')

        elif form_type == 'goals':
            goal_form = UserGoalForm(request.POST, instance=user_goal)
            if goal_form.is_valid():
                # Ensure goal is always linked to profile before saving
                goal = goal_form.save(commit=False)
                goal.user_profile = profile
                goal.save()
                messages.success(request, 'Goals updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the goals form.')

    else:
        # Initialize forms for GET request
        profile_form = UserProfileForm(instance=profile)
        goal_form = UserGoalForm(instance=user_goal)

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'goal_form': goal_form,
    }

    return render(request, 'account/edit_profile.html', context)

# Delete A profile
@login_required(login_url='account_login')
def delete_profile_view(request):
  
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Your profile has been deleted.')
        return redirect('account_logout')

    return render(request, 'account/delete_profile.html', {'profile': profile})
