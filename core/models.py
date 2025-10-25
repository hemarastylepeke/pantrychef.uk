from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from django.db.models.functions import Lower

User = settings.AUTH_USER_MODEL

# Records the types of foods details such as nuitritional info and general information about the food item
class Ingredient(models.Model):
    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy & Eggs'),
        ('meat', 'Meat & Poultry'),
        ('seafood', 'Seafood'),
        ('grains', 'Grains & Cereals'),
        ('legumes', 'Legumes & Nuts'),
        ('spices', 'Spices & Herbs'),
        ('condiments', 'Condiments & Sauces'),
        ('beverages', 'Beverages'),
        ('frozen', 'Frozen Foods'),
        ('bakery', 'Bakery'),
        ('canned', 'Canned Goods'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    typical_expiry_days = models.IntegerField(null=True, blank=True)
    storage_instructions = models.TextField(blank=True)
    calories = models.FloatField(help_text="Calories per 100g")
    protein = models.FloatField(help_text="Protein in grams per 100g")
    carbs = models.FloatField(help_text="Carbohydrates in grams per 100g")
    fat = models.FloatField(help_text="Fat in grams per 100g")
    fiber = models.FloatField(default=0, help_text="Fiber in grams per 100g")
    
    common_units = models.CharField(max_length=50, default="g")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['barcode']),
        ]

    def __str__(self):
        return self.name
    
    def get_nutritional_info(self):
        return f"Calories: {self.calories}, Protein: {self.protein}g, Carbs: {self.carbs}g, Fat: {self.fat}g"
    
    def get_nutritional_contribution(self, quantity: float, unit: str = None):
        """
        Estimate nutritional contribution for this ingredient based on quantity.

        Assumes that calories, protein, carbs, and fat values are per 100g/ml/piece.
        Adjust proportionally according to the quantity.
        """
        # Default assumption: nutrient values are per 100g
        factor = quantity / 100.0

        return {
            "calories": self.calories * factor,
            "protein": self.protein * factor,
            "carbs": self.carbs * factor,
            "fat": self.fat * factor,
        }

# Records to a particular user's  items that they own i.e Tomatoe sauce
class UserPantry(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('consumed', 'Consumed'),
        ('wasted', 'Wasted'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=200, blank=True)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    product_image = models.ImageField(upload_to='pantry_images/', blank=True, null=True)
    expiry_label_image = models.ImageField(upload_to='expiry_labels/', blank=True, null=True)
    
    detected_expiry_text = models.TextField(blank=True)
    detection_confidence = models.FloatField(null=True, blank=True)
    detection_source = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Entry'),
            ('vision_api', 'Google Vision API'),
            ('barcode', 'Barcode Scan'),
        ],
        default='manual'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User pantries"
        ordering = ['expiry_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['user', 'expiry_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.ingredient.name}"


class Recipe(models.Model):
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    CUISINE_CHOICES = [
        ('kenyan', 'Kenyan'),
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('asian', 'Asian'),
        ('indian', 'Indian'),
        ('mediterranean', 'Mediterranean'),
        ('american', 'American'),
        ('french', 'French'),
        ('thai', 'Thai'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS)
    prep_time = models.IntegerField(blank=True, null=True)  
    cook_time = models.IntegerField(blank=True, null=True) 
    cuisine = models.CharField(max_length=50, choices=CUISINE_CHOICES)
    servings = models.IntegerField()

    # Link recipes to ingredients using a ManyToMany through RecipeIngredient
    ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient', related_name='recipes')

    instructions = models.TextField()

    total_calories = models.FloatField(null=True, blank=True)
    total_protein = models.FloatField(null=True, blank=True)
    total_carbs = models.FloatField(null=True, blank=True)
    total_fat = models.FloatField(null=True, blank=True)

    dietary_tags = models.CharField(max_length=200, blank=True)

    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True)
    average_rating = models.FloatField(default=0)
    rating_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cuisine']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['average_rating']),
        ]

    def __str__(self):
        return self.name

    # Calculate nuitrional data to match user goals
    def calculate_nutrition(self):
        """
        Dynamically calculates total nutrition from linked ingredients.
        """
        recipe_ingredients = self.recipeingredient_set.all()
        total_calories = total_protein = total_carbs = total_fat = 0
        for ri in recipe_ingredients:
            contrib = ri.get_nutritional_contribution()
            total_calories += contrib['calories']
            total_protein += contrib['protein']
            total_carbs += contrib['carbs']
            total_fat += contrib['fat']
        self.total_calories = total_calories
        self.total_protein = total_protein
        self.total_carbs = total_carbs
        self.total_fat = total_fat
        self.save()


class RecipeIngredient(models.Model):
    """
    A bridge table linking recipes and ingredients. It stores the quantity, unit, and nutritional contribution of each ingredient used in a recipe.
    This relationship allows accurate nutrition calculation, cost tracking, and AI-driven recipe generation based on available ingredients,
    dietary preferences, and user budgets.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(max_length=50, default="g")
    
    optional = models.BooleanField(default=False, help_text="Whether ingredient is optional")

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity}{self.unit}) for {self.recipe.name}"

    def get_nutritional_contribution(self):
        """
        Returns nutritional info scaled to the quantity used.
        """
        scale = self.quantity / 100
        return {
            'calories': self.ingredient.calories * scale,
            'protein': self.ingredient.protein * scale,
            'carbs': self.ingredient.carbs * scale,
            'fat': self.ingredient.fat * scale,
        }


class ShoppingList(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'AI Generated'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default="Weekly Shopping List")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2)
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    pantry_utilization = models.FloatField(default=0)
    goal_alignment = models.FloatField(default=0)
    waste_reduction_score = models.FloatField(default=0)
    
    week_number = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    year = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['year', 'week_number']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.created_at.date()}"


class ShoppingListItem(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]
    
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    estimated_price = models.DecimalField(max_digits=8, decimal_places=2)
    actual_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    purchased = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    reason = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', 'ingredient__name']


class FoodWasteRecord(models.Model):
    WASTE_REASONS = [
        ('expired', 'Expired'),
        ('over_purchased', 'Over Purchased'),
        ('didnt_like', "Didn't Like"),
        ('recipe_change', 'Recipe Changed'),
        ('forgot_about', 'Forgot About It'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    original_quantity = models.FloatField()
    quantity_wasted = models.FloatField()
    unit = models.CharField(max_length=20)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.CharField(max_length=50, choices=WASTE_REASONS)
    reason_details = models.TextField(blank=True)
    
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    waste_date = models.DateField(auto_now_add=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-waste_date']
        indexes = [
            models.Index(fields=['user', 'waste_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.ingredient.name} waste"


# class ConsumptionRecord(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     pantry_item = models.ForeignKey(UserPantry, on_delete=models.CASCADE)
#     recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True)
#     quantity_used = models.FloatField()
#     date_consumed = models.DateField(auto_now_add=True)
#     notes = models.TextField(blank=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-date_consumed']


class ImageProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='processing_jobs/')
    job_type = models.CharField(max_length=20, choices=[('expiry', 'Expiry Date'), ('ingredient', 'Ingredient ID')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    detected_text = models.TextField(blank=True)
    processed_data = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class Budget(models.Model):
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('KES', 'KES'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='weekly')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency}/{self.period}"

    def get_spending_percentage(self):
        if self.amount > 0:
            return (self.amount_spent / self.amount) * 100
        return 0
    
    def get_remaining_budget(self):
        return self.amount - self.amount_spent
    
    def get_status_display(self):
        return "Active" if self.active else "Inactive"
    
    def get_confirmed_shopping_lists(self):
        """Get all confirmed shopping lists for this budget period"""
        return ShoppingList.objects.filter(
            user=self.user,
            status='confirmed',
            completed_at__date__gte=self.start_date,
            completed_at__date__lte=self.end_date if self.end_date else timezone.now().date()
        ).order_by('-completed_at')
    
    def get_total_spent_from_shopping_lists(self):
        """Calculate total spent from confirmed shopping lists in this period"""
        confirmed_lists = self.get_confirmed_shopping_lists()
        return confirmed_lists.aggregate(
            total=Sum('total_actual_cost')
        )['total'] or Decimal('0.00')
    
    def sync_amount_spent(self):
        """Sync amount_spent with actual shopping list data"""
        self.amount_spent = self.get_total_spent_from_shopping_lists()
        self.save()
        return self.amount_spent
    
    def get_spending_breakdown(self):
        """Get spending breakdown by category for analytics"""
        from django.db.models import Sum
        
        shopping_items = ShoppingListItem.objects.filter(
            shopping_list__user=self.user,
            shopping_list__status='confirmed',
            shopping_list__completed_at__date__gte=self.start_date,
            shopping_list__completed_at__date__lte=self.end_date if self.end_date else timezone.now().date(),
            purchased=True
        ).select_related('ingredient')
        
        category_breakdown = {}
        for item in shopping_items:
            actual_price = item.actual_price or item.estimated_price or Decimal('0.00')
            category = item.ingredient.category
            
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'amount': Decimal('0.00'),
                    'count': 0,
                    'items': []
                }
            
            category_breakdown[category]['amount'] += actual_price
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['items'].append({
                'name': item.ingredient.name,
                'amount': actual_price,
                'quantity': item.quantity
            })
        
        return category_breakdown