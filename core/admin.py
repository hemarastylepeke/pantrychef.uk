from django.contrib import admin
from .models import UserPantry, Ingredient, Recipe, ShoppingList, ConsumptionRecord, FoodWasteRecord, ShoppingListItem, ImageProcessingJob, RecipeIngredient 

admin.site.register(Ingredient)
admin.site.register(UserPantry)
admin.site.register(Recipe)
admin.site.register(ShoppingList)
admin.site.register(ShoppingListItem)
admin.site.register(ConsumptionRecord)
admin.site.register(FoodWasteRecord)
admin.site.register(ImageProcessingJob)
admin.site.register(RecipeIngredient)

