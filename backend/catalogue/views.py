from catalogue.models import AddOn, Plan
from catalogue.serializers import AddOnSerializer, PlanSerializer
from common.permissions import ReadAnyWriteRoles
from common.viewsets import TenantScopedViewSet


class PlanViewSet(TenantScopedViewSet):
    """Plans are gym-wide; receptionists are read-only."""

    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [ReadAnyWriteRoles]
    branch_scoped = False

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs


class AddOnViewSet(TenantScopedViewSet):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer
    permission_classes = [ReadAnyWriteRoles]
    branch_scoped = False

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs
