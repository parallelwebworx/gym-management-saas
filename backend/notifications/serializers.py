from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "member", "member_name", "membership", "payment", "event",
            "channel", "to_phone", "body", "status", "attempts",
            "provider_message_id", "error", "sent_at", "created_at",
        ]
