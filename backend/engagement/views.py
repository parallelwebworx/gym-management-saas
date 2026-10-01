from datetime import timedelta

from django.db.models import Sum
from rest_framework import mixins, viewsets
from rest_framework.views import APIView

from common.dates import ist_day_bounds_utc, ist_today
from common.permissions import IsAuthenticatedInGym
from common.responses import ok
from common.viewsets import EnvelopeResponseMixin
from engagement.models import Reminder
from engagement.serializers import ReminderSerializer
from memberships.models import Membership, MembershipStatus
from payments.models import Payment
from tenants.models import Role


class ReminderViewSet(
    EnvelopeResponseMixin, mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticatedInGym]

    def get_queryset(self):
        user = self.request.user
        qs = Reminder.objects.filter(gym_id=user.gym_id).select_related("created_by")
        if user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        if self.request.query_params.get("member"):
            qs = qs.filter(member_id=self.request.query_params["member"])
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(gym_id=user.gym_id, branch_id=user.branch_id, created_by=user)


class TodayView(APIView):
    """Role/branch-aware snapshot for the front desk."""

    permission_classes = [IsAuthenticatedInGym]

    def _scope(self, qs):
        user = self.request.user
        qs = qs.filter(gym_id=user.gym_id)
        if user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        return qs

    def _revenue(self, day):
        start, end = ist_day_bounds_utc(day)
        agg = self._scope(Payment.objects.all()).filter(
            created_at__gte=start, created_at__lt=end
        ).aggregate(total=Sum("amount_paise"))
        return agg["total"] or 0

    def _rows(self, memberships, today, reminders_by_member):
        out = []
        for m in memberships:
            out.append({
                "membership_id": m.id,
                "member_id": m.member_id,
                "member_name": m.member.full_name,
                "phone": m.member.phone,
                "plan_name": m.plan_name,
                "end_date": m.end_date.isoformat(),
                "days_left": (m.end_date - today).days,
                "last_reminded_at": reminders_by_member.get(m.member_id),
            })
        return out

    def get(self, request):
        today = ist_today()
        base = self._scope(Membership.objects.select_related("member").prefetch_related("freezes"))

        # Expiring soon: active (not cancelled, not frozen) ending within 14 days.
        expiring_candidates = base.filter(
            end_date__gte=today, end_date__lte=today + timedelta(days=14),
            cancel_effective_date__isnull=True,
        )
        expiring = [m for m in expiring_candidates if m.status_on(today, m.freezes.all()) == MembershipStatus.ACTIVE]

        # Recently expired: ended in the last 7 days, not cancelled.
        recent_candidates = base.filter(
            end_date__gte=today - timedelta(days=7), end_date__lt=today,
            cancel_effective_date__isnull=True,
        )
        recently_expired = [m for m in recent_candidates if m.status_on(today, m.freezes.all()) == MembershipStatus.EXPIRED]

        # Enrolled today (IST).
        start_utc, end_utc = ist_day_bounds_utc(today)
        enrolled_today = list(base.filter(created_at__gte=start_utc, created_at__lt=end_utc))

        # Frozen now.
        frozen = [m for m in base.filter(
            freezes__freeze_end_date__isnull=True, freezes__freeze_start_date__lte=today
        ).distinct() if m.status_on(today, m.freezes.all()) == MembershipStatus.FROZEN]

        # Last reminder per member across all rows shown.
        member_ids = {m.member_id for m in [*expiring, *recently_expired, *enrolled_today]}
        reminders_by_member = {}
        if member_ids:
            for r in self._scope(Reminder.objects.all()).filter(member_id__in=member_ids).order_by("member_id", "-created_at"):
                reminders_by_member.setdefault(r.member_id, r.created_at.isoformat())

        revenue_today = self._revenue(today)
        revenue_yesterday = self._revenue(today - timedelta(days=1))

        data = {
            "date": today.isoformat(),
            "metrics": {
                "revenue_today_paise": revenue_today,
                "revenue_delta_paise": revenue_today - revenue_yesterday,
                "new_enrollments_today": len(enrolled_today),
                "expiring_14d": len(expiring),
                "expiring_7d": sum(1 for m in expiring if (m.end_date - today).days <= 7),
                "expiring_3d": sum(1 for m in expiring if (m.end_date - today).days <= 3),
                "frozen_now": len(frozen),
            },
            "expiring_soon": self._rows(
                sorted(expiring, key=lambda m: m.end_date), today, reminders_by_member
            ),
            "recently_expired": self._rows(
                sorted(recently_expired, key=lambda m: m.end_date, reverse=True), today, reminders_by_member
            ),
            "enrolled_today": self._rows(enrolled_today, today, reminders_by_member),
        }
        return ok(data)
