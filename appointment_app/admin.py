from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import CustomUser, Booking

User = get_user_model()  # Ensure we are using CustomUser

@admin.action(description="Reset all users' booking limits")
def reset_booking_limits(modeladmin, request, queryset):
    queryset.update(booking_limit=3)

class CustomUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_deactivated", "booking_limit")  # Show in list
    list_filter = ("is_active", "is_deactivated")  # Add filter for deactivated users
    fieldsets = UserAdmin.fieldsets + (  # Add checkbox in edit form
        ("Account Settings", {"fields": ("is_deactivated", "booking_limit",)}),
    )
    actions = ["deactivate_users", "activate_users", reset_booking_limits]  # Bulk actions

    def deactivate_users(self, request, queryset):
        queryset.update(is_deactivated=True, is_active=False)
    deactivate_users.short_description = "Deactivate selected users"

    def activate_users(self, request, queryset):
        queryset.update(is_deactivated=False, is_active=True)
    activate_users.short_description = "Activate selected users"

# Unregister the old User model if it's still there
try:
    from django.contrib.auth.models import User as DefaultUser
    admin.site.unregister(DefaultUser)
except admin.sites.NotRegistered:
    pass  # If it’s not registered, ignore the error

# Register CustomUser instead
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Booking)
