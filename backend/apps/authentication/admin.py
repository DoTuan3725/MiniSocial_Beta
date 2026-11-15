from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "email_verified", "is_active", "created_at")
    list_filter = ("role", "email_verified", "is_active")
    search_fields = ("email", "full_name", "search_name")
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "search_name")
