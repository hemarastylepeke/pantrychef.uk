from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from allauth.account.forms import LoginForm
from allauth.exceptions import ImmediateHttpResponse

from .models import UserProfile


class CustomLoginForm(LoginForm):
    def login(self, request, redirect_url=None):
        try:
            self.request = request
            login_field = self.cleaned_data.get("login")
            password = self.cleaned_data.get("password")

            if login_field and password:
                user = authenticate(request, username=login_field, password=password)
                if user is None:
                    messages.error(request, "Invalid login credentials. Please try again.")
                elif not user.is_active:
                    messages.error(request, "Your account is inactive. Please contact support.")

            ret = super().login(request, redirect_url)
            messages.success(request, f"Welcome back, {self.user.email}!")
            return ret

        except ImmediateHttpResponse:
            if hasattr(self, 'user') and self.user and not self.user.is_active:
                messages.error(request, "Your account is not active.")
            elif not getattr(self, 'user', None):
                messages.error(request, "Invalid login credentials.")
            else:
                messages.error(request, "Login failed. Please try again.")
            raise

        except Exception:
            messages.error(request, "An unexpected error occurred during login. Please try again.")
            raise

    def clean(self):
        try:
            cleaned_data = super().clean()
            return cleaned_data
        except forms.ValidationError:
            if hasattr(self, 'request'):
                messages.error(self.request, "Authentication failed, please try again!")
            raise



class UserProfileForm(forms.ModelForm):
    """Handles general profile information such as name, image, and physical data."""
    class Meta:
        model = UserProfile
        fields = [
            'profile_image',
            'first_name',
            'last_name',
            'subscription_plan',
            'height',
            'weight',
            'age',
            'gender',
            'activity_level',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'subscription_plan': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Height (cm)'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Weight (kg)'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
        }


class DietaryRequirementsForm(forms.ModelForm):
    """Handles dietary-related information."""
    class Meta:
        model = UserProfile
        fields = [
            'allergies',
            'dietary_restrictions',
            'disliked_ingredients',
        ]
        widgets = {
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any allergies (e.g., peanuts, dairy)...'
            }),
            'dietary_restrictions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any dietary restrictions (e.g., vegan, halal)...'
            }),
            'disliked_ingredients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ingredients you prefer to avoid...'
            }),
        }


class PreferencesForm(forms.ModelForm):
    """Handles user taste preferences and cuisines."""
    class Meta:
        model = UserProfile
        fields = ['preferred_cuisines']
        widgets = {
            'preferred_cuisines': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List your favorite cuisines (e.g., Italian, Kenyan, Thai)...'
            }),
        }
