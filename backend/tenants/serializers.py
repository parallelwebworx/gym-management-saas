from rest_framework import serializers

from tenants.models import Branch, Gym, User


class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ["id", "name", "gstin", "invoice_prefix", "subscription_tier",
                  "notifications_enabled"]


class GymSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ["id", "name", "gstin", "invoice_prefix", "subscription_tier",
                  "notifications_enabled"]
        read_only_fields = ["id", "subscription_tier"]

    def validate_gstin(self, value):
        value = (value or "").strip().upper()
        if value and len(value) != 15:
            raise serializers.ValidationError("GSTIN must be 15 characters.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class MeSerializer(serializers.ModelSerializer):
    gym = GymSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "gym", "branch"]
