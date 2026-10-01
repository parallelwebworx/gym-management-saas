from django.contrib import admin

from engagement.models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "channel", "created_by", "created_at"]
    list_filter = ["channel"]
    search_fields = ["member__full_name", "note"]
