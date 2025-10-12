from django import forms
from .models import UserProfile
from django.contrib import messages
from allauth.account.forms import LoginForm
from django.contrib.auth import authenticate
from allauth.core.exceptions import ImmediateHttpResponse

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'first_name', 'last_name']


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