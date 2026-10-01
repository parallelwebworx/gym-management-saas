"""Settings endpoints: gym profile, branches, account, subscription."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, viewsets
from rest_framework.views import APIView

from common.permissions import IsAuthenticatedInGym, IsOwner
from common.responses import err, ok
from common.viewsets import EnvelopeResponseMixin
from members.models import Member
from tenants.export import export_response
from tenants.models import Branch
from tenants.serializers import (
    BranchSerializer,
    GymSettingsSerializer,
    PasswordChangeSerializer,
)


class DataExportView(APIView):
    permission_classes = [IsOwner]

    def get(self, request):
        return export_response(request.user.gym)


class GymSettingsView(APIView):
    permission_classes = [IsAuthenticatedInGym]

    def get(self, request):
        return ok(GymSettingsSerializer(request.user.gym).data)

    def patch(self, request):
        if request.user.role != "owner":
            return err("Only owners can edit gym settings.", code="forbidden", status=403)
        ser = GymSettingsSerializer(request.user.gym, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return ok(ser.data)


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticatedInGym]

    def get(self, request):
        gym = request.user.gym
        return ok({
            "tier": gym.subscription_tier,
            "whatsapp_enabled": gym.subscription_tier == "pro",
            "features": {
                "whatsapp": gym.subscription_tier == "pro",
                "multi_branch": True,
            },
        })


class AccountView(APIView):
    permission_classes = [IsAuthenticatedInGym]

    def patch(self, request):
        """Update the caller's own display name."""
        name = request.data.get("full_name")
        if name is not None:
            request.user.full_name = name
            request.user.save(update_fields=["full_name", "updated_at"])
        from tenants.serializers import MeSerializer
        return ok(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticatedInGym]

    def post(self, request):
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["current_password"]):
            return err("Current password is incorrect.", code="bad_password", status=400)
        try:
            validate_password(ser.validated_data["new_password"], user)
        except DjangoValidationError as exc:
            return err(" ".join(exc.messages), code="weak_password", status=400)
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return ok({"changed": True})


class BranchViewSet(
    EnvelopeResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """Branch management. Reads for any in-gym user; writes owner-only."""

    serializer_class = BranchSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedInGym()]
        return [IsOwner()]

    def get_queryset(self):
        return Branch.objects.filter(
            gym_id=self.request.user.gym_id, deleted_at__isnull=True
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(gym_id=self.request.user.gym_id)

    def update(self, request, *args, **kwargs):
        branch = self.get_object()
        deactivating = (
            request.data.get("is_active") is False and branch.is_active
        )
        if deactivating:
            reason = self._blocks_deactivation(branch)
            if reason:
                return err(reason, code="cannot_deactivate", status=409)
        return super().update(request, *args, **kwargs)

    def _blocks_deactivation(self, branch):
        active_branches = Branch.objects.filter(
            gym_id=branch.gym_id, is_active=True, deleted_at__isnull=True
        ).count()
        if active_branches <= 1:
            return "Cannot deactivate the last active branch."
        if Member.objects.filter(gym_id=branch.gym_id, branch_id=branch.id).exists():
            return "Cannot deactivate a branch that still has members. Reassign them first."
        if branch.users.filter(is_active=True, deleted_at__isnull=True).exists():
            return "Cannot deactivate a branch that still has staff assigned."
        return None
