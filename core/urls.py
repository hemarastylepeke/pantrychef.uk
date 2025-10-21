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

    path('pantry/add-manual/', views.add_manual_ingredient_view, name='add_manual_ingredient'),
    path('pantry/scan/', views.scan_ingredient_view, name='scan_ingredient'),
    path('pantry/<int:item_id>/update-quantity/', views.update_quantity, name='update_quantity'),
    path('pantry/<int:item_id>/consume/', views.log_consumption_view, name='log_consumption'),
    path('pantry/<int:item_id>/waste/', views.record_waste_view, name='record_waste'),
    path('pantry/<int:item_id>/quick-consume/', views.quick_consume, name='quick_consume'),
    
    # Analytics
    path('pantry/analytics/', views.pantry_analytics_view, name='pantry_analytics'),
    
    # API endpoints
    path('api/pantry/expiring-soon/', views.expiring_soon_api, name='expiring_soon_api'),
]