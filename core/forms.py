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
            'unit': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
                'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
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
        self.fields['unit'].choices = [
            ('g', 'grams'), ('kg', 'kilograms'), 
            ('ml', 'milliliters'), ('l', 'liters'),
            ('pieces', 'pieces'), ('cups', 'cups'),
            ('tbsp', 'tablespoons'), ('tsp', 'teaspoons')
        ]

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
    quantity = forms.FloatField(min_value=0, widget=forms.NumberInput(attrs={
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
            ('tbsp', 'tablespoons'), ('tsp', 'teaspoons')
        ]

class ConsumptionForm(forms.Form):
    quantity_used = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
            'step': '0.01'
        })
    )
    recipe = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in view
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
            'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
            'rows': 2, 
            'placeholder': 'How was it used?'
        })
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Recipe
        super().__init__(*args, **kwargs)
        self.fields['recipe'].queryset = Recipe.objects.all()

class WasteRecordForm(forms.Form):
    quantity_wasted = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors',
            'step': '0.01'
        })
    )
    reason = forms.ChoiceField(
        choices=FoodWasteRecord.WASTE_REASONS,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors appearance-none bg-no-repeat bg-right pr-10',
            'style': "background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 20 20\"><path stroke=\"%236b7280\" stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"1.5\" d=\"m6 8 4 4 4-4\"/></svg>'); background-position: right 0.75rem center; background-size: 1.5em 1.5em;"
        })
    )
    reason_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors resize-vertical min-h-[100px]',
            'rows': 2, 
            'placeholder': 'Why was this wasted?'
        })
    )