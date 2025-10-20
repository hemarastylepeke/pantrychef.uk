from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserProfile
from .forms import UserProfileForm, DietaryRequirementsForm, PreferencesForm

# Create profile view
@login_required(login_url='account_login')
def create_profile_view(request):
    """
    Allow a user to manually create a profile after account creation.
    """
    # Prevent duplicate profiles
    if UserProfile.objects.filter(user=request.user).exists():
        messages.info(request, 'You already have a profile.')
        return redirect('profile_page')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Your profile was created successfully!')
            return redirect('profile_page')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm()

    return render(request, 'account/create_profile.html', {'form': form})


# View and update profile
@login_required(login_url='account_login')
def profile_page_view(request):
    """
    Display and update the user's profile if it exists.
    If it doesn't exist, redirect to profile creation.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')

    profile_form = UserProfileForm(instance=profile)
    dietary_form = DietaryRequirementsForm(instance=profile)
    preferences_form = PreferencesForm(instance=profile)

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

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'dietary_form': dietary_form,
        'preferences_form': preferences_form,
    }
    return render(request, 'account/profile.html', context)


@login_required(login_url='account_login')
def edit_profile_view(request):
    """
    Edit profile view that handles all three forms in a tabbed interface
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Initialize forms with instance data
    profile_form = UserProfileForm(instance=profile)
    dietary_form = DietaryRequirementsForm(instance=profile)
    preferences_form = PreferencesForm(instance=profile)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = UserProfileForm(
                request.POST, 
                request.FILES, 
                instance=profile
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Personal information updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the personal information form.')

        elif form_type == 'dietary':
            dietary_form = DietaryRequirementsForm(
                request.POST, 
                instance=profile
            )
            if dietary_form.is_valid():
                dietary_form.save()
                messages.success(request, 'Dietary requirements updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the dietary requirements form.')

        elif form_type == 'preferences':
            preferences_form = PreferencesForm(
                request.POST, 
                instance=profile
            )
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Taste preferences updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the preferences form.')

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'dietary_form': dietary_form,
        'preferences_form': preferences_form,
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
