from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(email, password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserAccountManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    SUBSCRIPTION_PLANS = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('pro', 'Pro'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        blank=True, 
        null=True, 
        default='profile_images/default_profile_image.png'
    )
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='basic')
    
    # Personal information for nutritional calculations
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")  
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    activity_level = models.CharField(
        max_length=20, 
        choices=[
            ('sedentary', 'Sedentary'), # inactive
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('active', 'Very Active'),
            ('athlete', 'Athlete')
        ],
        null=True, 
        blank=True
    )
    
    # Dietary requirements
    allergies = models.JSONField(default=list, blank=True, help_text="List of food allergies")
    dietary_restrictions = models.JSONField(
        default=list, 
        blank=True, 
        help_text="e.g., vegetarian, vegan, gluten-free"
    )
    disliked_ingredients = models.JSONField(default=list, blank=True)
    preferred_cuisines = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

class UserGoal(models.Model):
    GOAL_TYPES = [
        ('LOSE_WEIGHT', 'Lose Weight'),
        ('GAIN_WEIGHT', 'Gain Weight'),
        ('BUILD_MUSCLE', 'Build Muscle'),
        ('MAINTAIN_WEIGHT', 'Maintain Weight'),
        ('MORE_FIBER', 'More Fiber'),
        ('MORE_IRON', 'More Iron'),
        ('MORE_VEGGIES', 'More Vegetables'),
        ('REDUCE_WASTE', 'Reduce Food Waste'),
        ('BUDGET_FRIENDLY', 'Budget Friendly'),
    ]
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_value = models.FloatField(null=True, blank=True, help_text="Target weight or specific metric")
    current_value = models.FloatField(null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    target_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="1-5, with 5 being highest priority")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-created_at']

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
    ]
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='WEEKLY')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency}/{self.period}"