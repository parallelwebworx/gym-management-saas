from datetime import date

from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from common.permissions import IsOwnerOrManager
from common.viewsets import EnvelopeResponseMixin
from common.xlsx import xlsx_response
from tenants.models import Role


class AuditLogViewSet(
    EnvelopeResponseMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """Append-only audit trail viewer. Owner/manager only; branch-aware."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsOwnerOrManager]

    def get_queryset(self):
        user = self.request.user
        qs = AuditLog.objects.filter(gym_id=user.gym_id).select_related("actor")
        if user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        p = self.request.query_params
        if p.get("action"):
            qs = qs.filter(action=p["action"])
        if p.get("entity_type"):
            qs = qs.filter(entity_type=p["entity_type"])
        if p.get("entity_id"):
            qs = qs.filter(entity_id=p["entity_id"])
        if p.get("actor"):
            qs = qs.filter(actor_id=p["actor"])
        for key, lookup in (("from", "created_at__date__gte"), ("to", "created_at__date__lte")):
            if p.get(key):
                try:
                    qs = qs.filter(**{lookup: date.fromisoformat(p[key])})
                except ValueError:
                    pass
        return qs

    @action(detail=False, methods=["get"])
    def export(self, request):
        rows = (
            (a.created_at.isoformat(), a.action, a.entity_type, a.entity_id,
             (a.actor.email if a.actor else ""), a.summary)
            for a in self.get_queryset().iterator()
        )
        return xlsx_response(
            "audit_log.xlsx",
            ["Timestamp", "Action", "Entity", "Entity ID", "Actor", "Summary"],
            rows, sheet_title="Audit",
        )
