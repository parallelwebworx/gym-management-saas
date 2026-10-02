from rest_framework import serializers

from catalogue.models import AddOn, Plan


class _CIUniqueNameMixin:
    """Case-insensitive, per-gym, alive uniqueness check on ``name``."""

    model = None

    def validate_name(self, value):
        request = self.context["request"]
        qs = self.model.objects.filter(
            gym_id=request.user.gym_id, name__iexact=value.strip()
        )
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"A {self.model.__name__.lower()} with this name already exists."
            )
        return value.strip()


class PlanSerializer(_CIUniqueNameMixin, serializers.ModelSerializer):
    model = Plan

    class Meta:
        model = Plan
        fields = [
            "id", "name", "plan_type", "duration_days", "price_paise",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_duration_days(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be at least 1 day.")
        return value


class AddOnSerializer(_CIUniqueNameMixin, serializers.ModelSerializer):
    model = AddOn

    class Meta:
        model = AddOn
        fields = [
            "id", "name", "addon_type", "price_paise",
            "auto_apply_on_first_enrollment", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
