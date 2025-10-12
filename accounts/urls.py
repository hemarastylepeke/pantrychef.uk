from django.urls import path, include
from .views import (
    profile_page_view, 
    edit_goal_view, 
    delete_goal_view,
    update_goal_progress_ajax,
    quick_budget_update_ajax
)

urlpatterns = [
    # Main profile page with all functionality
    path('profile/', profile_page_view, name='profile_page'),
    
    # Goal management
    path('goals/<int:goal_id>/edit/', edit_goal_view, name='edit_goal'),
    path('goals/<int:goal_id>/delete/', delete_goal_view, name='delete_goal'),
    
    # AJAX endpoints for dynamic updates
    path('goals/<int:goal_id>/update-progress/', update_goal_progress_ajax, name='update_goal_progress'),
    path('budget/quick-update/', quick_budget_update_ajax, name='quick_budget_update'),
]
# urlpatterns = [
#     path('accounts/login/', views.login_view, name='account_login'),
#     path('accounts/signup/', views.signup_view, name='account_signup'),
#     path('accounts/logout/', views.logout_view, name='account_logout'),
#     path('accounts/password/reset/', views.password_reset_view, name='account_reset_password'),
#     path('accounts/password/reset/done/', views.password_reset_done_view, name='account_reset_password_done'),
#     path('accounts/password/change/', views.password_change_view, name='account_change_password'),
#     path('accounts/password/change/done/', views.password_change_done_view, name='account_change_password_done'),
#     path('accounts/password/reset/key/<uidb36>/<key>/', views.password_reset_from_key_view, name='account_reset_password_from_key'),
# ]
# Only for reference in the projects templates Below are the urls for the accounts app

# accounts/login
# accounts/signup/
# accounts/logout/
# accounts/password/reset/
# accounts/password/reset/done/
# accounts/password/change/
# accounts/password/change/done/
# accounts/password/reset/key/<uidb36>/<key>/