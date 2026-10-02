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
    FROZEN = "frozen", "Frozen"


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

    def is_frozen_on(self, today=None, freezes=None) -> bool:
        """True if an (open or still-running) freeze covers ``today``.

        ``freezes`` may be a prefetched iterable to avoid an extra query in lists.
        """
        today = today or ist_today()
        rows = freezes if freezes is not None else self.freezes.all()
        for f in rows:
            if f.freeze_start_date <= today and (
                f.freeze_end_date is None or today < f.freeze_end_date
            ):
                return True
        return False

    def status_on(self, today=None, freezes=None) -> str:
        today = today or ist_today()
        # Precedence: cancelled > frozen > active > expired.
        if self.cancel_effective_date and today >= self.cancel_effective_date:
            return MembershipStatus.CANCELLED
        if self.is_frozen_on(today, freezes):
            return MembershipStatus.FROZEN
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


class Freeze(TenantScoped):
    """
    A pause on an active membership. While a freeze is open (no end date) and has
    started, the membership reads as FROZEN. On unfreeze, ``days_added`` records
    the frozen-day count and the membership's ``end_date`` is extended by exactly
    that many days — so ``Σ days_added`` always equals ``end_date - original_end_date``.
    ``completed`` is derived at read time (a freeze is completed once it has an end).
    """

    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="freezes")
    freeze_start_date = models.DateField()
    freeze_end_date = models.DateField(null=True, blank=True)
    days_added = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="freezes_created"
    )

    class Meta:
        ordering = ["-freeze_start_date"]
        indexes = [models.Index(fields=["gym", "membership"])]

    @property
    def completed(self) -> bool:
        return self.freeze_end_date is not None

    def __str__(self):
        return f"freeze m={self.membership_id} {self.freeze_start_date}→{self.freeze_end_date or 'open'}"


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
