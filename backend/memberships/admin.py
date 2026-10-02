from django.contrib import admin

from memberships.models import Membership, MembershipAddOn


class AddOnInline(admin.TabularInline):
    model = MembershipAddOn
    extra = 0


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "plan_name", "start_date", "end_date", "correction_count"]
    list_filter = ["plan_name"]
    search_fields = ["member__full_name", "member__phone"]
    inlines = [AddOnInline]
