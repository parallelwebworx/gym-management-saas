from rest_framework import serializers

from engagement.models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Reminder
        fields = [
            "id", "member", "membership", "channel", "note",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]
