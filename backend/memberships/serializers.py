from rest_framework import serializers

from memberships.models import Membership, MembershipAddOn
from payments.models import net_paid_for_membership


class MembershipAddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipAddOn
        fields = ["id", "addon", "name", "addon_type", "price_paise", "auto_applied"]


class MembershipSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    addons = MembershipAddOnSerializer(many=True, read_only=True)
    net_paid_paise = serializers.SerializerMethodField()
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id", "member", "member_name", "plan", "plan_name", "duration_days",
            "plan_price_paise", "start_date", "end_date", "original_end_date",
            "status", "correction_count", "cancelled_at", "cancel_effective_date",
            "cancel_reason", "previous", "addons", "net_paid_paise", "created_at",
        ]

    def get_net_paid_paise(self, obj):
        return net_paid_for_membership(obj)
