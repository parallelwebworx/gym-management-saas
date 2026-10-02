from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from common.permissions import IsAuthenticatedInGym, IsOwner
from common.phone import normalize_phone_in
from common.responses import err, ok
from common.viewsets import EnvelopeResponseMixin
from notifications import templates_registry as templates
from notifications.models import (
    Notification,
    NotificationChannel,
    NotificationEvent,
    NotificationStatus,
)
from notifications.serializers import NotificationSerializer
from notifications.tasks import send_notification_task
from tenants.models import Role


class NotificationViewSet(
    EnvelopeResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedInGym]

    def get_permissions(self):
        if self.action in ("resend", "test_message"):
            return [IsOwner()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.filter(gym_id=user.gym_id).select_related("member")
        if user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        p = self.request.query_params
        for key in ("member", "membership", "status", "event"):
            if p.get(key):
                qs = qs.filter(**{key: p[key]})
        return qs

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        note = self.get_queryset().filter(pk=pk).first()
        if not note:
            return err("Notification not found.", code="not_found", status=404)
        note.status = NotificationStatus.PENDING
        note.error = ""
        note.save(update_fields=["status", "error", "updated_at"])
        send_notification_task.delay(note.id)
        note.refresh_from_db()
        return ok(NotificationSerializer(note).data)

    @action(detail=False, methods=["post"], url_path="test")
    def test_message(self, request):
        raw = request.data.get("phone", "")
        try:
            phone = normalize_phone_in(raw)
        except ValueError as exc:
            return err(str(exc), code="invalid_phone")
        user = request.user
        channel = request.data.get("channel", NotificationChannel.SMS)
        if channel == NotificationChannel.WHATSAPP and user.gym.subscription_tier != "pro":
            channel = NotificationChannel.SMS
        body = templates.render("test", {"gym_name": user.gym.name})
        note = Notification.objects.create(
            gym=user.gym, branch=user.branch, event=NotificationEvent.TEST,
            channel=channel, to_phone=phone, body=body,
            template_version=templates.TEMPLATE_VERSION,
        )
        send_notification_task.delay(note.id)
        note.refresh_from_db()
        return ok(NotificationSerializer(note).data, status=201)
