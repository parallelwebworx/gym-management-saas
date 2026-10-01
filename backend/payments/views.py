from datetime import date

from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from common.errors import ServiceError
from common.permissions import IsAuthenticatedInGym, IsOwner
from common.responses import err, ok
from common.viewsets import EnvelopeResponseMixin
from payments.models import Payment, PaymentKind, create_refund
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    EnvelopeResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Payments ledger (read) + owner-only refund / edit actions."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedInGym]

    def get_permissions(self):
        if self.action in ("refund", "edit"):
            return [IsOwner()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.filter(gym_id=user.gym_id).select_related("member", "created_by")
        if user.role != "owner" and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        p = self.request.query_params
        if p.get("member"):
            qs = qs.filter(member_id=p["member"])
        if p.get("membership"):
            qs = qs.filter(membership_id=p["membership"])
        if p.get("kind"):
            qs = qs.filter(kind=p["kind"])
        if p.get("from"):
            try:
                qs = qs.filter(created_at__date__gte=date.fromisoformat(p["from"]))
            except ValueError:
                pass
        if p.get("to"):
            try:
                qs = qs.filter(created_at__date__lte=date.fromisoformat(p["to"]))
            except ValueError:
                pass
        return qs

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        user = request.user
        original = self.get_queryset().filter(pk=pk).first()
        if not original:
            return err("Payment not found.", code="not_found", status=404)
        if original.kind == PaymentKind.REFUND:
            return err("Cannot refund a refund.", code="bad_target")
        try:
            amount = int(request.data.get("amount_paise", 0))
            refund = create_refund(
                original=original, amount_paise=amount,
                reason=request.data.get("reason", ""), actor=user, gym=user.gym,
            )
        except (ValueError, ServiceError) as e:
            msg = getattr(e, "message", str(e))
            code = getattr(e, "code", "bad_refund")
            return err(msg, code=code)

        from audit import services as audit
        from audit.models import AuditAction
        audit.record(
            actor=user, action=AuditAction.REFUND, entity=refund,
            after={"amount_paise": refund.amount_paise, "invoice": refund.invoice_number,
                   "refund_of": original.invoice_number, "reason": refund.reason},
            summary=f"Refunded {refund.invoice_number}",
        )
        from notifications.models import NotificationEvent
        from notifications.service import queue_notification
        queue_notification(
            gym=user.gym, event=NotificationEvent.REFUND,
            member=refund.member, membership=refund.membership, payment=refund,
        )
        return ok({"refund": PaymentSerializer(refund).data}, status=201)

    @action(detail=True, methods=["post"])
    def edit(self, request, pk=None):
        from audit import services as audit
        from audit.models import AuditAction

        user = request.user
        payment = self.get_queryset().filter(pk=pk).first()
        if not payment:
            return err("Payment not found.", code="not_found", status=404)
        if payment.kind == PaymentKind.REFUND:
            return err("Refund rows cannot be edited.", code="bad_target")
        reason = request.data.get("reason", "").strip()
        if not reason:
            return err("An edit reason is required.", code="missing_reason")
        try:
            new_amount = int(request.data["amount_paise"])
        except (KeyError, ValueError):
            return err("amount_paise is required and must be an integer.", code="bad_amount")
        if new_amount <= 0:
            return err("Edited amount must be positive.", code="bad_amount")

        before = {"amount_paise": payment.amount_paise}
        payment.mark_edited(new_amount, reason)
        audit.record(
            actor=user, action=AuditAction.EDIT_PAYMENT, entity=payment,
            before=before, after={"amount_paise": new_amount, "reason": reason},
            summary="Edited payment amount",
        )
        return ok(PaymentSerializer(payment).data)
