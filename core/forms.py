from django import forms
from .models import UserPantry, Ingredient, ConsumptionRecord, FoodWasteRecord

class PantryItemForm(forms.ModelForm):
    class Meta:
        model = UserPantry
        fields = [
            'ingredient', 'custom_name', 'quantity', 'unit', 
            'purchase_date', 'expiry_date', 'price',
            'product_image', 'expiry_label_image', 'notes'
        ]
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-select'}),
            'custom_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Custom name (optional)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any additional notes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].choices = [
            ('g', 'grams'), ('kg', 'kilograms'), 
            ('ml', 'milliliters'), ('l', 'liters'),
            ('pieces', 'pieces'), ('cups', 'cups'),
            ('tbsp', 'tablespoons'), ('tsp', 'teaspoons')
        ]

class ManualIngredientForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    custom_name = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    category = forms.ChoiceField(choices=Ingredient.CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = forms.FloatField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    unit = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-select'}))
    purchase_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    price = forms.DecimalField(max_digits=8, decimal_places=2, required=False, 
                              widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    typical_expiry_days = forms.IntegerField(required=False, 
                                           widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].choices = [
            ('g', 'grams'), ('kg', 'kilograms'), 
            ('ml', 'milliliters'), ('l', 'liters'),
            ('pieces', 'pieces'), ('cups', 'cups'),
            ('tbsp', 'tablespoons'), ('tsp', 'teaspoons')
        ]

class ConsumptionForm(forms.Form):
    quantity_used = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    recipe = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in view
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'How was it used?'})
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Recipe
        super().__init__(*args, **kwargs)
        self.fields['recipe'].queryset = Recipe.objects.all()

class WasteRecordForm(forms.Form):
    quantity_wasted = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    reason = forms.ChoiceField(
        choices=FoodWasteRecord.WASTE_REASONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Why was this wasted?'})
    )