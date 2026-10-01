"""
Payments ledger + per-gym invoice sequencing.

Money is a SIGNED integer in paise: positive rows are payments, negative rows are
refunds. Net revenue for any slice = ``Sum(amount_paise)``. DB CheckConstraints
back these invariants so a bad row can never be written, even by a bug.

Invoice numbers are sequential PER GYM PER YEAR, formatted ``{prefix}-{year}-{seq}``
and allocated under a row lock inside the enrolling transaction (see
``allocate_invoice_number``) so concurrent enrollments can never collide.
"""
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from common.models import TenantScoped


class PaymentKind(models.TextChoices):
    ENROLLMENT = "enrollment", "Enrollment"
    RENEWAL = "renewal", "Renewal"
    REFUND = "refund", "Refund"
    ADJUSTMENT = "adjustment", "Adjustment"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    BANK = "bank", "Bank transfer"
    OTHER = "other", "Other"


class InvoiceSequence(models.Model):
    """One counter row per (gym, year). ``last_value`` is the last number issued."""

    gym = models.ForeignKey("tenants.Gym", on_delete=models.CASCADE, related_name="invoice_sequences")
    year = models.PositiveIntegerField()
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["gym", "year"], name="uniq_invoice_seq_gym_year")
        ]

    def __str__(self):
        return f"gym={self.gym_id} {self.year}: {self.last_value}"


def allocate_invoice_number(gym, when=None) -> str:
    """Allocate the next sequential invoice number for ``gym``.

    MUST be called inside a ``transaction.atomic()`` block; it takes a row lock on
    the (gym, year) counter via ``select_for_update`` so concurrent callers queue
    rather than collide.
    """
    when = when or timezone.now()
    year = when.year
    seq_row, _ = InvoiceSequence.objects.select_for_update().get_or_create(
        gym=gym, year=year
    )
    seq_row.last_value += 1
    seq_row.save(update_fields=["last_value"])
    prefix = (gym.invoice_prefix or "INV").strip()
    return f"{prefix}-{year}-{seq_row.last_value:04d}"


class Payment(TenantScoped):
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="payments")
    membership = models.ForeignKey(
        "memberships.Membership", on_delete=models.PROTECT,
        related_name="payments", null=True, blank=True,
    )
    kind = models.CharField(max_length=20, choices=PaymentKind.choices, default=PaymentKind.ENROLLMENT)
    method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)

    # Signed: payments > 0, refunds < 0.
    amount_paise = models.IntegerField()
    # Discount granted on this transaction (>= 0). Tracked for leakage reports.
    discount_paise = models.PositiveIntegerField(default=0)

    invoice_number = models.CharField(max_length=40)
    refund_of = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="refunds"
    )
    reason = models.CharField(max_length=255, blank=True, default="")

    # Edit bookkeeping (owner-only edits keep an immutable trail).
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    original_amount_paise = models.IntegerField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="payments_created"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["gym", "invoice_number"], name="uniq_payment_invoice_per_gym"),
            models.CheckConstraint(condition=~models.Q(amount_paise=0), name="payment_amount_nonzero"),
            # Refunds are strictly negative; every other kind is strictly positive.
            models.CheckConstraint(
                condition=(
                    models.Q(kind="refund", amount_paise__lt=0)
                    | (~models.Q(kind="refund") & models.Q(amount_paise__gt=0))
                ),
                name="payment_sign_matches_kind",
            ),
            # A refund must link to the payment it reverses; others must not.
            models.CheckConstraint(
                condition=(
                    models.Q(kind="refund", refund_of__isnull=False)
                    | (~models.Q(kind="refund") & models.Q(refund_of__isnull=True))
                ),
                name="refund_requires_link",
            ),
        ]
        indexes = [
            models.Index(fields=["gym", "-created_at"]),
            models.Index(fields=["gym", "member"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} {self.amount_paise}p"

    def mark_edited(self, new_amount_paise, reason):
        if not self.edited:
            self.original_amount_paise = self.amount_paise
        self.amount_paise = new_amount_paise
        self.reason = reason
        self.edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=[
            "amount_paise", "reason", "edited", "edited_at",
            "original_amount_paise", "updated_at",
        ])


def net_paid_for_membership(membership) -> int:
    """Net amount paid (payments minus refunds) for a membership, in paise."""
    agg = Payment.objects.filter(membership=membership).aggregate(
        total=models.Sum("amount_paise")
    )
    return agg["total"] or 0


@transaction.atomic
def create_refund(*, original: Payment, amount_paise: int, reason: str, actor, gym):
    """Create a signed-negative refund row linked to ``original``.

    ``amount_paise`` is the positive magnitude to refund; it must not exceed the
    membership's remaining net balance.
    """
    if amount_paise <= 0:
        raise ValueError("Refund amount must be positive.")
    remaining = net_paid_for_membership(original.membership)
    if amount_paise > remaining:
        raise ValueError(
            f"Refund exceeds remaining balance ({remaining} paise)."
        )
    invoice = allocate_invoice_number(gym)
    return Payment.objects.create(
        gym=gym,
        branch=original.branch,
        member=original.member,
        membership=original.membership,
        kind=PaymentKind.REFUND,
        method=original.method,
        amount_paise=-amount_paise,
        invoice_number=invoice,
        refund_of=original,
        reason=reason,
        created_by=actor,
    )
