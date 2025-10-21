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

    # Budget management URLs
    path('budgets/', views.budget_list_view, name='budget_list'),
    path('budgets/add/', views.create_budget_view, name='create_budget'),
    path('budgets/<int:budget_id>/', views.budget_detail_view, name='budget_detail'),
    path('budgets/<int:budget_id>/edit/', views.edit_budget_view, name='edit_budget'),
    path('budgets/<int:budget_id>/delete/', views.delete_budget_view, name='delete_budget'),
    path('budgets/<int:budget_id>/toggle-active/', views.toggle_budget_active_view, name='toggle_budget_active'),
    path('budgets/analytics/', views.budget_analytics_view, name='budget_analytics'),

    # Shopping list URLs
    path('shopping-lists/', views.shopping_list_list_view, name='shopping_list_list'),
    path('shopping-lists/<int:list_id>/', views.shopping_list_detail_view, name='shopping_list_detail'),
]