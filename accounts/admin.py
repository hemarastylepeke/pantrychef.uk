from .models import UserAccount, UserProfile
from django.contrib import admin

# Register account models
admin.site.register(UserAccount)
admin.site.register(UserProfile)
