from django.urls import path
from . import views

urlpatterns = [
    # Pantry management
    path('pantry/', views.pantry_dashboard_view, name='pantry_dashboard'),

    # Pantry item operations
    path('pantry/list/', views.pantry_list_view, name='pantry_list'),
    path('pantry/add/', views.add_pantry_item_view, name='add_pantry_item'),
    path('pantry/edit/<int:item_id>/', views.edit_pantry_item_view, name='edit_pantry_item'),
    path('pantry/delete/<int:item_id>/', views.delete_pantry_item_view, name='delete_pantry_item'),

    # Ingredient management URLs
    path('ingredients/', views.ingredient_list_view, name='ingredient_list'),
    path('ingredients/add/', views.add_ingredient_view, name='add_ingredient'),
    path('ingredients/<int:ingredient_id>/', views.ingredient_detail_view, name='ingredient_detail'),
    path('ingredients/<int:ingredient_id>/edit/', views.edit_ingredient_view, name='edit_ingredient'),
    path('ingredients/<int:ingredient_id>/delete/', views.delete_ingredient_view, name='delete_ingredient'),
]