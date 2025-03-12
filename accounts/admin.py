from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser  # Define the model
    
    # Display these fields in the user list
    list_display = ("username", "email", "phone_number", "email_confirmation", "is_staff", "is_active")
    
    # Add phone_number and email_confirmation to fieldsets (for editing an existing user)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("phone_number", "email_confirmation")}),
    )

    # Add phone_number and email_confirmation to add_fieldsets (for adding a new user)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("phone_number", "email_confirmation")}),
    )

# Register CustomUser with Django Admin
admin.site.register(CustomUser, CustomUserAdmin)
