from django import forms
from .models import UserProfile, UserGoal, Budget
from django.contrib import messages
from allauth.account.forms import LoginForm
from django.contrib.auth import authenticate
from allauth.core.exceptions import ImmediateHttpResponse
from django.utils import timezone

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'profile_image', 'first_name', 'last_name',
            'height', 'weight', 'age', 'gender', 'activity_level'
        ]
        widgets = {
            'height': forms.NumberInput(attrs={
                'step': '0.1', 
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Height in cm'
            }),
            'weight': forms.NumberInput(attrs={
                'step': '0.1', 
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Weight in kg'
            }),
            'age': forms.NumberInput(attrs={
                'min': '1', 
                'max': '120',
                'class': 'form-control',
                'placeholder': 'Your age'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
        }
    
    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height and height <= 0:
            raise forms.ValidationError("Height must be a positive number")
        return height
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and weight <= 0:
            raise forms.ValidationError("Weight must be a positive number")
        return weight
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and (age < 1 or age > 120):
            raise forms.ValidationError("Age must be between 1 and 120")
        return age

class DietaryRequirementsForm(forms.ModelForm):
    # Common allergies and restrictions for checkboxes
    COMMON_ALLERGIES = [
        ('peanuts', 'Peanuts'),
        ('tree_nuts', 'Tree Nuts'),
        ('dairy', 'Dairy'),
        ('eggs', 'Eggs'),
        ('soy', 'Soy'),
        ('wheat', 'Wheat/Gluten'),
        ('fish', 'Fish'),
        ('shellfish', 'Shellfish'),
        ('sesame', 'Sesame'),
    ]
    
    COMMON_RESTRICTIONS = [
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('gluten_free', 'Gluten-Free'),
        ('dairy_free', 'Dairy-Free'),
        ('low_carb', 'Low Carb'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('halal', 'Halal'),
        ('kosher', 'Kosher'),
    ]
    
    COMMON_CUISINES = [
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('asian', 'Asian'),
        ('indian', 'Indian'),
        ('mediterranean', 'Mediterranean'),
        ('american', 'American'),
        ('thai', 'Thai'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese'),
        ('french', 'French'),
    ]
    
    allergies = forms.MultipleChoiceField(
        choices=COMMON_ALLERGIES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Food Allergies"
    )
    
    dietary_restrictions = forms.MultipleChoiceField(
        choices=COMMON_RESTRICTIONS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Dietary Restrictions"
    )
    
    preferred_cuisines = forms.MultipleChoiceField(
        choices=COMMON_CUISINES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Preferred Cuisines"
    )
    
    disliked_ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'class': 'form-control',
            'placeholder': 'Enter ingredients you dislike, separated by commas (e.g., cilantro, olives, mushrooms)'
        }),
        required=False,
        help_text="Separate with commas"
    )
    
    class Meta:
        model = UserProfile
        fields = ['allergies', 'dietary_restrictions', 'disliked_ingredients', 'preferred_cuisines']
    
    
class UserGoalForm(forms.ModelForm):
    class Meta:
        model = UserGoal
        fields = ['goal_type', 'target_value', 'target_date', 'priority', 'current_value']
        widgets = {
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={
                'step': '0.1', 
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Target value'
            }),
            'current_value': forms.NumberInput(attrs={
                'step': '0.1', 
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Current value'
            }),
            'target_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            # Change from Select → TextInput
            'priority': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter priority (e.g. High, Medium, Low)'
            }),
        }
        labels = {
            'current_value': 'Current Progress',
            'target_value': 'Target Value',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make current_value optional for new goals
        if not self.instance.pk:
            self.fields['current_value'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        goal_type = cleaned_data.get('goal_type')
        target_value = cleaned_data.get('target_value')
        current_value = cleaned_data.get('current_value', 0)
        target_date = cleaned_data.get('target_date')
        
        # Validate weight-related goals
        if goal_type in ['LOSE_WEIGHT', 'GAIN_WEIGHT', 'BUILD_MUSCLE']:
            if not target_value:
                raise forms.ValidationError({
                    'target_value': 'Target value is required for weight-related goals'
                })
            if target_value <= 0:
                raise forms.ValidationError({
                    'target_value': 'Target value must be positive'
                })
        
        # Validate target date
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError({
                'target_date': 'Target date cannot be in the past'
            })
        
        # Validate current value doesn't exceed target
        if target_value and current_value and current_value > target_value:
            if goal_type == 'LOSE_WEIGHT':
                raise forms.ValidationError({
                    'current_value': 'Current weight cannot be higher than target weight for weight loss goals'
                })
        
        return cleaned_data


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount', 'period', 'currency']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0',
                'class': 'form-control',
                'placeholder': 'Enter budget amount'
            }),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'amount': 'Budget Amount',
            'period': 'Budget Period',
            'currency': 'Currency',
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Budget amount must be positive")
        return amount

class PreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_cuisines', 'activity_level', 'subscription_plan']
        widgets = {
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'subscription_plan': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the same cuisine choices as DietaryRequirementsForm
        self.fields['preferred_cuisines'] = forms.MultipleChoiceField(
            choices=DietaryRequirementsForm.COMMON_CUISINES,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            required=False,
            label="Preferred Cuisines",
            initial=self.instance.preferred_cuisines if self.instance.pk else []
        )

class CustomLoginForm(LoginForm):
    def login(self, request, redirect_url=None):
        try:
            # Store the request for use in error handling
            self.request = request
            
            # Check if user exists and account is active before attempting login
            login_field = self.cleaned_data.get("login")
            password = self.cleaned_data.get("password")
            
            if login_field and password:
                # Try to authenticate to check for specific error conditions
                user = authenticate(request, username=login_field, password=password)
                if user is None:
                    messages.error(request, "Invalid login credentials. Please try again.")
                elif not user.is_active:
                    messages.error(request, "Your account is inactive. Please contact support.")
            
            # Call the original login method
            ret = super().login(request, redirect_url)
            
            # If we get here, login was successful
            messages.success(request, f"Welcome back, {self.user.email}!")

            return ret
            
        except ImmediateHttpResponse:
            # This exception is raised by allauth for various login issues
            if hasattr(self, 'user') and self.user and not self.user.is_active:
                messages.error(request, "Your account is not active.")
            elif not getattr(self, 'user', None):
                messages.error(request, "Invalid login credentials.")
            else:
                messages.error(request, "Login failed. Please try again.")
            # Re-raise to maintain allauth's flow
            raise
            
        except Exception as e:
            # Catch any other login-related errors
            messages.error(request, "An unexpected error occurred during login. Please try again.")
            raise

    def clean(self):
        # Override clean method to add custom validation messages
        try:
            cleaned_data = super().clean()
            return cleaned_data
        except forms.ValidationError as e:
            # Add error messages for form validation failures
            if hasattr(self, 'request'):
                messages.error(self.request, "Authentication failed, please try again!")
            raise