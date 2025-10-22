from django import forms
from .models import UserPantry, Ingredient, Recipe, Budget, ShoppingList, ShoppingListItem
from django.utils import timezone

class PantryItemForm(forms.ModelForm):
    class Meta:
        model = UserPantry
        fields = [
            'ingredient', 'custom_name', 'quantity', 'unit',
            'purchase_date', 'expiry_date', 'price',
            'product_image', 'expiry_label_image', 'notes'
        ]
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'custom_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Custom name (optional)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Enter unit (e.g., grams, bottles, packs, cups)'
            }),
            'purchase_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 2,
                'placeholder': 'Any additional notes...'
            }),
            'product_image': forms.FileInput(attrs={
                'class': 'absolute inset-0 w-full h-full opacity-0 cursor-pointer'
            }),
            'expiry_label_image': forms.FileInput(attrs={
                'class': 'absolute inset-0 w-full h-full opacity-0 cursor-pointer'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional for edit scenarios
        self.fields['product_image'].required = False
        self.fields['expiry_label_image'].required = False
        self.fields['price'].required = False
        self.fields['custom_name'].required = False
        
        # Set initial values for date fields if empty
        if not self.instance.pk:  # Create mode
            self.fields['purchase_date'].initial = timezone.now().date()
            self.fields['expiry_date'].initial = timezone.now().date() + timezone.timedelta(days=7)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0")
        return quantity

    def clean_expiry_date(self):
        purchase_date = self.cleaned_data.get('purchase_date')
        expiry_date = self.cleaned_data.get('expiry_date')
        
        if purchase_date and expiry_date and expiry_date < purchase_date:
            raise forms.ValidationError("Expiry date cannot be before purchase date")
        
        return expiry_date


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            'name', 'category', 'barcode', 'typical_expiry_days', 
            'storage_instructions', 'calories', 'protein', 'carbs', 
            'fat', 'fiber', 'common_units'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Enter ingredient name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Barcode (optional)'
            }),
            'typical_expiry_days': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Typical expiry days'
            }),
            'storage_instructions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 3,
                'placeholder': 'Storage instructions...'
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1',
                'placeholder': 'Calories per 100g'
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1',
                'placeholder': 'Protein per 100g'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1',
                'placeholder': 'Carbs per 100g'
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1',
                'placeholder': 'Fat per 100g'
            }),
            'fiber': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1',
                'placeholder': 'Fiber per 100g'
            }),
            'common_units': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Common units (e.g., g, ml, pieces)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make optional fields
        self.fields['barcode'].required = False
        self.fields['typical_expiry_days'].required = False
        self.fields['storage_instructions'].required = False
        self.fields['fiber'].required = False

    def clean_calories(self):
        calories = self.cleaned_data.get('calories')
        if calories and calories < 0:
            raise forms.ValidationError("Calories cannot be negative")
        return calories

    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Check for duplicate barcode
            if Ingredient.objects.filter(barcode=barcode).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError("An ingredient with this barcode already exists")
        return barcode


# Add this to your forms.py
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount', 'period', 'currency', 'start_date', 'end_date', 'active']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'period': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['end_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date")
        
        return cleaned_data

class ShoppingListForm(forms.ModelForm):
    class Meta:
        model = ShoppingList
        fields = ['name', 'budget_limit', 'week_number', 'month', 'year', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Enter shopping list name'
            }),
            'budget_limit': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'week_number': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'min': '1',
                'max': '52'
            }),
            'month': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'min': '1',
                'max': '12'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'min': '2020',
                'max': '2030'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year as default
        current_year = timezone.now().year
        self.fields['year'].initial = current_year
        self.fields['week_number'].initial = timezone.now().isocalendar()[1]
        self.fields['month'].initial = timezone.now().month


class ShoppingListItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = ['ingredient', 'quantity', 'unit', 'estimated_price', 'priority', 'notes', 'reason']
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'e.g., g, ml, pieces'
            }),
            'estimated_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Why is this item needed?'
            }),
        }


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'name', 'description', 'difficulty', 'prep_time', 'cook_time',
            'cuisine', 'servings', 'ingredients', 'instructions',
            'total_calories', 'total_protein', 'total_carbs', 'total_fat',
            'dietary_tags', 'image', 'is_ai_generated'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Enter recipe name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 3,
                'placeholder': 'Describe your recipe...'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'prep_time': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Preparation time in minutes'
            }),
            'cook_time': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Cooking time in minutes'
            }),
            'cuisine': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'Number of servings'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[200px] font-mono text-sm',
                'rows': 8,
                'placeholder': 'List ingredients with quantities, one per line:\n• 2 cups flour\n• 1 tsp salt\n• 3 eggs'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[200px]',
                'rows': 8,
                'placeholder': 'Write step-by-step instructions...'
            }),
            'total_calories': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '1'
            }),
            'total_protein': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1'
            }),
            'total_carbs': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1'
            }),
            'total_fat': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.1'
            }),
            'dietary_tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'placeholder': 'e.g., vegetarian, gluten-free, low-carb'
            }),
            'image': forms.FileInput(attrs={
                'class': 'absolute inset-0 w-full h-full opacity-0 cursor-pointer'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make nutritional fields optional
        self.fields['total_calories'].required = False
        self.fields['total_protein'].required = False
        self.fields['total_carbs'].required = False
        self.fields['total_fat'].required = False
        self.fields['dietary_tags'].required = False
        self.fields['image'].required = False

    def clean_prep_time(self):
        prep_time = self.cleaned_data.get('prep_time')
        if prep_time and prep_time < 0:
            raise forms.ValidationError("Preparation time cannot be negative")
        return prep_time

    def clean_cook_time(self):
        cook_time = self.cleaned_data.get('cook_time')
        if cook_time and cook_time < 0:
            raise forms.ValidationError("Cooking time cannot be negative")
        return cook_time

    def clean_servings(self):
        servings = self.cleaned_data.get('servings')
        if servings and servings <= 0:
            raise forms.ValidationError("Servings must be greater than 0")
        return servings        