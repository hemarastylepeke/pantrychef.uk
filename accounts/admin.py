from .models import UserAccount, UserProfile, UserGoal, Budget
from django.contrib import admin

# Register account models
admin.site.register(UserAccount)
admin.site.register(UserProfile)
admin.site.register(UserGoal)
admin.site.register(Budget)