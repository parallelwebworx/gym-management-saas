from django.contrib import admin

from members.models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "phone", "gym", "branch", "created_at"]
    list_filter = ["gender"]
    search_fields = ["full_name", "phone", "email"]
