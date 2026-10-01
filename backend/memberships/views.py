from datetime import date

from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from common.errors import ServiceError
from common.permissions import IsAuthenticatedInGym, IsOwner
from common.responses import err, ok
from common.viewsets import EnvelopeResponseMixin
from members.serializers import MemberSerializer
from memberships import services
from memberships.models import Membership
from memberships.permissions import can_correct_membership
from memberships.serializers import MembershipSerializer
from payments.serializers import PaymentSerializer


def _parse_date(value, field="date"):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ServiceError(f"Invalid {field}: expected YYYY-MM-DD.", code="bad_date") from exc


class MembershipViewSet(
    EnvelopeResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read + revenue-loop actions. Memberships are created via `enroll`/`renew`,
    never via a plain POST."""

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticatedInGym]

    def get_permissions(self):
        if self.action == "cancel":
            return [IsOwner()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = (
            Membership.objects.filter(gym_id=user.gym_id)
            .select_related("member")
            .prefetch_related("addons")
        )
        if user.role != "owner" and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        member_id = self.request.query_params.get("member")
        if member_id:
            qs = qs.filter(member_id=member_id)
        return qs

    def _envelope(self, membership, payment=None, extra=None, status=200):
        data = {"membership": MembershipSerializer(membership, context={"request": self.request}).data}
        if payment is not None:
            data["payment"] = PaymentSerializer(payment).data
        if extra:
            data.update(extra)
        return ok(data, status=status)

    @action(detail=False, methods=["post"])
    def enroll(self, request):
        user = request.user
        body = request.data
        try:
            member_id = body.get("member_id")
            # Combined add + enroll: accept an inline new member.
            if not member_id and body.get("member"):
                ser = MemberSerializer(data=body["member"], context={"request": request})
                ser.is_valid(raise_exception=True)
                member = ser.save(gym_id=user.gym_id, branch_id=user.branch_id)
                member_id = member.id
            membership, payment = services.enroll(
                gym=user.gym, actor=user, member_id=member_id,
                plan_id=body.get("plan_id"),
                addon_ids=body.get("addon_ids", []),
                discount_paise=int(body.get("discount_paise", 0)),
                method=body.get("method", "cash"),
                amount_paid_paise=(
                    int(body["amount_paid_paise"]) if body.get("amount_paid_paise") is not None else None
                ),
                start_date=_parse_date(body.get("start_date"), "start_date"),
                expected_total_paise=(
                    int(body["expected_total_paise"]) if body.get("expected_total_paise") is not None else None
                ),
            )
        except ServiceError as e:
            return err(e.message, code=e.code, status=e.status)
        return self._envelope(membership, payment, status=201)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        user = request.user
        body = request.data
        try:
            membership, payment = services.renew(
                gym=user.gym, actor=user, membership_id=pk,
                plan_id=body.get("plan_id"),
                addon_ids=body.get("addon_ids", []),
                discount_paise=int(body.get("discount_paise", 0)),
                method=body.get("method", "cash"),
                amount_paid_paise=(
                    int(body["amount_paid_paise"]) if body.get("amount_paid_paise") is not None else None
                ),
                start_mode=body.get("start_mode", "from_previous_end"),
                custom_start_date=_parse_date(body.get("custom_start_date"), "custom_start_date"),
                expected_total_paise=(
                    int(body["expected_total_paise"]) if body.get("expected_total_paise") is not None else None
                ),
            )
        except ServiceError as e:
            return err(e.message, code=e.code, status=e.status)
        return self._envelope(membership, payment, status=201)

    @action(detail=True, methods=["post"])
    def correct(self, request, pk=None):
        user = request.user
        body = request.data
        try:
            membership = services.correct_membership(
                gym=user.gym, actor=user, membership_id=pk,
                plan_id=body.get("plan_id"),
                start_date=_parse_date(body.get("start_date"), "start_date"),
                addon_ids=body.get("addon_ids"),
                reason=body.get("reason", ""),
            )
        except ServiceError as e:
            return err(e.message, code=e.code, status=e.status)
        return self._envelope(membership)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        user = request.user
        body = request.data
        effective = _parse_date(body.get("effective_date"), "effective_date") if isinstance(body.get("effective_date"), str) else None
        try:
            if effective is None:
                raise ServiceError("effective_date is required (YYYY-MM-DD).", code="missing_date")
            membership, refund = services.cancel_membership(
                gym=user.gym, actor=user, membership_id=pk,
                effective_date=effective,
                prorated_refund=bool(body.get("prorated_refund", False)),
                method=body.get("method", "cash"),
                reason=body.get("reason", ""),
            )
        except ServiceError as e:
            return err(e.message, code=e.code, status=e.status)
        extra = {"refund": PaymentSerializer(refund).data} if refund else {}
        return self._envelope(membership, extra=extra)

    @action(detail=True, methods=["get"], url_path="can-correct")
    def can_correct(self, request, pk=None):
        membership = self.get_object()
        allowed, why = can_correct_membership(request.user, membership)
        return ok({"allowed": allowed, "reason": why})
