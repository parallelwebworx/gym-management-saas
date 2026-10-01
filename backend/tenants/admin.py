from django.contrib import admin

from tenants.models import Branch, Gym, User


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "subscription_tier", "created_at"]
    search_fields = ["name", "gstin"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gym", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "role", "gym", "branch", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "full_name"]
