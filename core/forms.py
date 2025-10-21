from django import forms
from .models import UserPantry, Ingredient, ConsumptionRecord, FoodWasteRecord, Recipe

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
            from django.utils import timezone
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


class ManualIngredientForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
        'placeholder': 'Enter ingredient name'
    }))
    custom_name = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
        'placeholder': 'Custom name (optional)'
    }))
    category = forms.ChoiceField(choices=Ingredient.CATEGORY_CHOICES, widget=forms.Select(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
        'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
    }))
    quantity = forms.FloatField(min_value=0.01, widget=forms.NumberInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
        'step': '0.01'
    }))
    unit = forms.ChoiceField(choices=[], widget=forms.Select(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
        'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
    }))
    purchase_date = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
    }))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
    }))
    price = forms.DecimalField(max_digits=8, decimal_places=2, required=False, 
                              widget=forms.NumberInput(attrs={
                                  'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                                  'step': '0.01'
                              }))
    typical_expiry_days = forms.IntegerField(required=False, 
                                           widget=forms.NumberInput(attrs={
                                               'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors'
                                           }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].choices = [
            ('g', 'grams'), ('kg', 'kilograms'), 
            ('ml', 'milliliters'), ('l', 'liters'),
            ('pieces', 'pieces'), ('cups', 'cups'),
            ('tbsp', 'tablespoons'), ('tsp', 'teaspoons'),
            ('bottles', 'bottles'), ('packs', 'packs'),
            ('cans', 'cans'), ('jars', 'jars')
        ]
        
        # Set initial dates
        from django.utils import timezone
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


class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = ConsumptionRecord
        fields = ['quantity_used', 'recipe', 'notes']
        widgets = {
            'quantity_used': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0.01'
            }),
            'recipe': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 2, 
                'placeholder': 'How was it used?'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        pantry_item = kwargs.pop('pantry_item', None)
        super().__init__(*args, **kwargs)
        
        # Filter recipes by user if available
        if user:
            self.fields['recipe'].queryset = Recipe.objects.filter(
                models.Q(created_by=user) | models.Q(created_by__isnull=True)
            )
        else:
            self.fields['recipe'].queryset = Recipe.objects.all()
        
        # Set max quantity based on pantry item
        if pantry_item:
            self.fields['quantity_used'].widget.attrs['max'] = pantry_item.quantity
            self.fields['quantity_used'].help_text = f"Maximum available: {pantry_item.quantity} {pantry_item.unit}"

    def clean_quantity_used(self):
        quantity_used = self.cleaned_data.get('quantity_used')
        if quantity_used <= 0:
            raise forms.ValidationError("Quantity used must be greater than 0")
        return quantity_used


class WasteRecordForm(forms.ModelForm):
    class Meta:
        model = FoodWasteRecord
        fields = ['quantity_wasted', 'reason', 'reason_details']
        widgets = {
            'quantity_wasted': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
                'step': '0.01',
                'min': '0.01'
            }),
            'reason': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
            }),
            'reason_details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
                'rows': 2, 
                'placeholder': 'Why was this wasted?'
            }),
        }

    def __init__(self, *args, **kwargs):
        pantry_item = kwargs.pop('pantry_item', None)
        super().__init__(*args, **kwargs)
        
        # Set max quantity based on pantry item
        if pantry_item:
            self.fields['quantity_wasted'].widget.attrs['max'] = pantry_item.quantity
            self.fields['quantity_wasted'].help_text = f"Maximum available: {pantry_item.quantity} {pantry_item.unit}"

    def clean_quantity_wasted(self):
        quantity_wasted = self.cleaned_data.get('quantity_wasted')
        if quantity_wasted <= 0:
            raise forms.ValidationError("Quantity wasted must be greater than 0")
        return quantity_wasted


# Optional: Quick Edit Form for simple updates
class QuickEditPantryForm(forms.ModelForm):
    class Meta:
        model = UserPantry
        fields = ['quantity', 'expiry_date', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 resize-vertical',
                'rows': 2,
                'placeholder': 'Quick notes...'
            }),
        }