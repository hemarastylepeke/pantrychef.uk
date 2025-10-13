from django.urls import path
from . import views

urlpatterns = [
    # Pantry management
    path('pantry/', views.pantry_dashboard, name='pantry_dashboard'),
    path('pantry/add/', views.add_pantry_item, name='add_pantry_item'),
    path('pantry/add-manual/', views.add_manual_ingredient, name='add_manual_ingredient'),
    path('pantry/scan/', views.scan_ingredient, name='scan_ingredient'),
    path('pantry/<int:item_id>/edit/', views.edit_pantry_item, name='edit_pantry_item'),
    path('pantry/<int:item_id>/update-quantity/', views.update_quantity, name='update_quantity'),
    path('pantry/<int:item_id>/consume/', views.log_consumption, name='log_consumption'),
    path('pantry/<int:item_id>/waste/', views.record_waste, name='record_waste'),
    path('pantry/<int:item_id>/quick-consume/', views.quick_consume, name='quick_consume'),
    path('pantry/<int:item_id>/delete/', views.delete_pantry_item, name='delete_pantry_item'),
    
    # Analytics
    path('pantry/analytics/', views.pantry_analytics, name='pantry_analytics'),
    
    # API endpoints
    path('api/pantry/expiring-soon/', views.expiring_soon_api, name='expiring_soon_api'),
]