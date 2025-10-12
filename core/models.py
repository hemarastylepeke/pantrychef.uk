from django.db import models
from accounts.models import UserAccount

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
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    typical_expiry_days = models.IntegerField(null=True, blank=True)
    storage_instructions = models.TextField(blank=True)
    
    # Nutritional information per 100g
    nutritional_info = models.JSONField(default=dict, blank=True)  # {calories: 50, protein: 2.5, carbs: 10, ...}
    
    # Common units for this ingredient
    common_units = models.JSONField(default=list, blank=True)  # ['g', 'kg', 'pieces', 'ml', 'l']
    
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

class UserPantry(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('consumed', 'Consumed'),
        ('wasted', 'Wasted'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=200, blank=True)  # User's custom name
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Image handling
    product_image = models.ImageField(upload_to='pantry_images/', blank=True, null=True)
    expiry_label_image = models.ImageField(upload_to='expiry_labels/', blank=True, null=True)
    
    # Detection data
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
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]
    
    CUISINE_CHOICES = [
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
    prep_time = models.IntegerField(help_text="Preparation time in minutes")
    cook_time = models.IntegerField(help_text="Cooking time in minutes")
    cuisine = models.CharField(max_length=50, choices=CUISINE_CHOICES)
    servings = models.IntegerField()
    
    # Ingredients with quantities
    ingredients = models.JSONField(default=list)  # [{ingredient_id: 1, quantity: 200, unit: 'g', name: 'Tomatoes'}, ...]
    
    # Step-by-step instructions
    instructions = models.JSONField(default=list)  # [{step: 1, instruction: 'Chop vegetables', duration: 5}, ...]
    
    # Nutritional information per serving
    nutritional_info = models.JSONField(default=dict)  # {calories: 350, protein: 20, ...}
    
    # Dietary tags for filtering
    dietary_tags = models.JSONField(default=list)  # ['vegetarian', 'gluten-free', 'high-protein']
    
    # Images
    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True)
    
    # Ratings and popularity
    average_rating = models.FloatField(default=0)
    rating_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cuisine']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['dietary_tags']),
        ]

    def __str__(self):
        return self.name

class ShoppingList(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'AI Generated'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default="Weekly Shopping List")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Budget information
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2)
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # AI generation metrics
    ai_metrics = models.JSONField(default=dict, blank=True)  # {pantry_utilization: 0.75, goal_alignment: 0.9, ...}
    
    # Period tracking
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
        return f"{self.user.email} - {self.name} - {self.created_at.date()}"

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
    
    # Reason for inclusion
    reason = models.CharField(max_length=200, blank=True)  # e.g., "for pasta recipe", "restocking"
    
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
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
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
        return f"{self.user.email} - {self.ingredient.name} waste"

class ConsumptionRecord(models.Model):
    """Track when users consume ingredients through recipes"""
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    pantry_item = models.ForeignKey(UserPantry, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_used = models.FloatField()
    date_consumed = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_consumed']

class ImageProcessingJob(models.Model):
    """Track image processing jobs for expiry date detection"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='processing_jobs/')
    job_type = models.CharField(max_length=20, choices=[('expiry', 'Expiry Date'), ('ingredient', 'Ingredient ID')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    detected_text = models.TextField(blank=True)
    processed_data = models.JSONField(default=dict, blank=True)  # {expiry_date: '2024-01-15', confidence: 0.85}
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']