from rest_framework import serializers

from memberships.models import Freeze, Membership, MembershipAddOn
from payments.models import net_paid_for_membership


class MembershipAddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipAddOn
        fields = ["id", "addon", "name", "addon_type", "price_paise", "auto_applied"]


class FreezeSerializer(serializers.ModelSerializer):
    completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Freeze
        fields = [
            "id", "freeze_start_date", "freeze_end_date", "days_added",
            "reason", "completed", "created_at",
        ]


class MembershipSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    addons = MembershipAddOnSerializer(many=True, read_only=True)
    freezes = FreezeSerializer(many=True, read_only=True)
    net_paid_paise = serializers.SerializerMethodField()
    total_days_added = serializers.SerializerMethodField()
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id", "member", "member_name", "plan", "plan_name", "duration_days",
            "plan_price_paise", "start_date", "end_date", "original_end_date",
            "status", "correction_count", "cancelled_at", "cancel_effective_date",
            "cancel_reason", "previous", "addons", "freezes", "net_paid_paise",
            "total_days_added", "created_at",
        ]

    def get_status(self, obj):
        # Uses the prefetched freezes (see the viewset) to avoid an extra query.
        return obj.status_on(freezes=obj.freezes.all())

    def get_net_paid_paise(self, obj):
        return net_paid_for_membership(obj)

    def get_total_days_added(self, obj):
        return sum(f.days_added for f in obj.freezes.all())
