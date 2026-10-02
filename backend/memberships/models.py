"""
Membership — a member's enrollment into a plan for a date window.

Key invariants (ported from the source app):
- ``original_end_date`` is set once at enrollment and never changes; ``end_date``
  may shift (freeze in Phase 3, correction/cancel here).
- Effective status (active / expired / cancelled) is COMPUTED ON READ from dates —
  never stored, never cron-updated. (``frozen`` arrives with Phase 3.)
- At most one *active* membership per member at a time (enforced in the enroll /
  renew services under a row lock, since "active" is a computed concept).

Plan details are snapshotted at enrollment so later catalogue edits don't rewrite
history.
"""
from django.conf import settings
from django.db import models

from common.dates import ist_today
from common.models import TenantScoped


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"
    # FROZEN arrives in Phase 3.


class Membership(TenantScoped):
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="memberships")
    plan = models.ForeignKey("catalogue.Plan", on_delete=models.PROTECT, related_name="memberships")

    # Snapshots taken at enrollment (history must not change if the plan changes).
    plan_name = models.CharField(max_length=120)
    duration_days = models.PositiveIntegerField()
    plan_price_paise = models.PositiveIntegerField()

    start_date = models.DateField()
    end_date = models.DateField()
    original_end_date = models.DateField(editable=False)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_effective_date = models.DateField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True, default="")

    correction_count = models.PositiveIntegerField(default=0)
    previous = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="renewals"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="memberships_created"
    )

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["gym", "member"]),
            models.Index(fields=["gym", "end_date"]),
        ]

    def save(self, *args, **kwargs):
        # Pin original_end_date once, on first write.
        if self._state.adding and not self.original_end_date:
            self.original_end_date = self.end_date
        super().save(*args, **kwargs)

    def status_on(self, today=None) -> str:
        today = today or ist_today()
        if self.cancel_effective_date and today >= self.cancel_effective_date:
            return MembershipStatus.CANCELLED
        if today <= self.end_date:
            return MembershipStatus.ACTIVE
        return MembershipStatus.EXPIRED

    @property
    def status(self) -> str:
        return self.status_on()

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE

    def __str__(self):
        return f"{self.member_id} {self.plan_name} {self.start_date}→{self.end_date}"


class MembershipAddOn(TenantScoped):
    """Add-ons attached to a membership, snapshotted at enrollment time."""

    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="addons")
    addon = models.ForeignKey("catalogue.AddOn", on_delete=models.PROTECT, related_name="membership_addons")
    name = models.CharField(max_length=120)
    addon_type = models.CharField(max_length=20)
    price_paise = models.PositiveIntegerField()
    auto_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} @ {self.price_paise}p"
