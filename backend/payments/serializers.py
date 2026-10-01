from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "member", "member_name", "membership", "kind", "method",
            "amount_paise", "discount_paise", "invoice_number", "refund_of",
            "reason", "edited", "edited_at", "original_amount_paise",
            "created_by", "created_by_name", "created_at",
        ]
