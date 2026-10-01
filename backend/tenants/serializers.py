from rest_framework import serializers

from tenants.models import Branch, Gym, User


class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ["id", "name", "gstin", "invoice_prefix", "subscription_tier"]


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
