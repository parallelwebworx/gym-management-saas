from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "event", "channel", "to_phone", "status", "attempts", "created_at"]
    list_filter = ["event", "channel", "status"]
    search_fields = ["to_phone", "body"]
