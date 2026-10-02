from rest_framework import serializers

from common.phone import normalize_phone_in
from members.models import Member


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "id", "full_name", "phone", "email", "gender",
            "date_of_birth", "address", "notes",
            "branch", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "branch", "created_at", "updated_at"]

    def validate_phone(self, value):
        try:
            return normalize_phone_in(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate(self, attrs):
        """Reject a duplicate phone within the gym (among live rows)."""
        request = self.context["request"]
        phone = attrs.get("phone")
        if phone:
            qs = Member.objects.filter(gym_id=request.user.gym_id, phone=phone)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"phone": "A member with this phone number already exists."}
                )
        return attrs
