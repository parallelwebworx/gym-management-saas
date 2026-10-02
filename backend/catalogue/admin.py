from django.contrib import admin

from catalogue.models import AddOn, Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gym", "plan_type", "duration_days", "price_paise", "is_active"]
    list_filter = ["plan_type", "is_active"]
    search_fields = ["name"]


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gym", "addon_type", "price_paise",
                    "auto_apply_on_first_enrollment", "is_active"]
    list_filter = ["addon_type", "is_active", "auto_apply_on_first_enrollment"]
    search_fields = ["name"]
