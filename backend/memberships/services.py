"""
Revenue-loop services. Every mutation here is atomic and audited. All money is
integer paise and is ALWAYS recomputed server-side from catalogue IDs — client
line totals are never trusted.
"""
from datetime import timedelta

from django.db import transaction

from audit import services as audit
from audit.models import AuditAction
from catalogue.models import AddOn, Plan
from common.dates import ist_today
from common.errors import ServiceError
from members.models import Member
from memberships.models import Membership, MembershipAddOn, MembershipStatus
from memberships.permissions import can_correct_membership
from payments.models import (
    Payment,
    PaymentKind,
    allocate_invoice_number,
    create_refund,
    net_paid_for_membership,
)


def _resolve_addons(gym, addon_ids):
    addon_ids = list(dict.fromkeys(addon_ids or []))  # dedupe, keep order
    addons = list(AddOn.objects.filter(gym=gym, id__in=addon_ids, is_active=True))
    if len(addons) != len(addon_ids):
        raise ServiceError("One or more add-ons are invalid or inactive.", code="invalid_addon")
    return addons


def _active_memberships_locked(member):
    """Lock the member's memberships and return those currently active."""
    rows = list(Membership.objects.select_for_update().filter(member=member))
    return rows, [m for m in rows if m.status == MembershipStatus.ACTIVE]


def _price_enrollment(plan, selected_addons, auto_addons, discount_paise, expected_total_paise):
    subtotal = plan.price_paise + sum(a.price_paise for a in selected_addons) \
        + sum(a.price_paise for a in auto_addons)
    total = subtotal - discount_paise
    if discount_paise < 0:
        raise ServiceError("Discount cannot be negative.", code="bad_discount")
    if total < 0:
        raise ServiceError("Discount exceeds the order total.", code="bad_discount")
    if expected_total_paise is not None and expected_total_paise != total:
        # Anti-tamper: the client's view of the total disagrees with the server.
        raise ServiceError(
            "Order total has changed; please review before paying.", code="amount_mismatch"
        )
    return subtotal, total


def _create_membership_with_payment(
    *, gym, actor, member, plan, selected_addons, auto_addons,
    discount_paise, method, amount_paid_paise, total, start_date, kind, previous=None,
):
    end_date = start_date + timedelta(days=plan.duration_days)
    membership = Membership.objects.create(
        gym=gym, branch=member.branch, member=member, plan=plan,
        plan_name=plan.name, duration_days=plan.duration_days, plan_price_paise=plan.price_paise,
        start_date=start_date, end_date=end_date, created_by=actor, previous=previous,
    )
    for a in [*selected_addons, *auto_addons]:
        MembershipAddOn.objects.create(
            gym=gym, branch=member.branch, membership=membership, addon=a,
            name=a.name, addon_type=a.addon_type, price_paise=a.price_paise,
            auto_applied=a in auto_addons,
        )

    payment = None
    if amount_paid_paise > 0:
        invoice = allocate_invoice_number(gym)
        payment = Payment.objects.create(
            gym=gym, branch=member.branch, member=member, membership=membership,
            kind=kind, method=method, amount_paise=amount_paid_paise,
            discount_paise=discount_paise, invoice_number=invoice, created_by=actor,
        )
    return membership, payment


@transaction.atomic
def enroll(*, gym, actor, member_id, plan_id, addon_ids=None, discount_paise=0,
           method="cash", amount_paid_paise=None, start_date=None, expected_total_paise=None):
    member = Member.objects.select_for_update().filter(gym=gym, id=member_id).first()
    if not member:
        raise ServiceError("Member not found.", code="not_found", status=404)
    plan = Plan.objects.filter(gym=gym, id=plan_id, is_active=True).first()
    if not plan:
        raise ServiceError("Plan not found or inactive.", code="invalid_plan")

    all_memberships, active = _active_memberships_locked(member)
    if active:
        raise ServiceError(
            "This member already has an active membership.", code="member_has_active_membership"
        )

    selected = _resolve_addons(gym, addon_ids)
    first_enrollment = len(all_memberships) == 0
    auto_addons = []
    if first_enrollment:
        selected_ids = {a.id for a in selected}
        auto_addons = [
            a for a in AddOn.objects.filter(
                gym=gym, is_active=True, auto_apply_on_first_enrollment=True
            ) if a.id not in selected_ids
        ]

    _subtotal, total = _price_enrollment(plan, selected, auto_addons, discount_paise, expected_total_paise)
    amount = total if amount_paid_paise is None else amount_paid_paise
    if amount < 0 or amount > total:
        raise ServiceError("Amount paid must be between 0 and the order total.", code="bad_amount")

    start = start_date or ist_today()
    membership, payment = _create_membership_with_payment(
        gym=gym, actor=actor, member=member, plan=plan, selected_addons=selected,
        auto_addons=auto_addons, discount_paise=discount_paise, method=method,
        amount_paid_paise=amount, total=total, start_date=start, kind=PaymentKind.ENROLLMENT,
    )
    audit.record(
        actor=actor, action=AuditAction.ENROLL, entity=membership,
        after={"plan": plan.name, "total_paise": total, "paid_paise": amount},
        summary=f"Enrolled in {plan.name}",
    )
    return membership, payment


@transaction.atomic
def renew(*, gym, actor, membership_id, plan_id, addon_ids=None, discount_paise=0,
          method="cash", amount_paid_paise=None, start_mode="from_previous_end",
          custom_start_date=None, expected_total_paise=None):
    previous = Membership.objects.select_for_update().filter(gym=gym, id=membership_id).first()
    if not previous:
        raise ServiceError("Membership not found.", code="not_found", status=404)
    member = Member.objects.select_for_update().get(pk=previous.member_id)
    plan = Plan.objects.filter(gym=gym, id=plan_id, is_active=True).first()
    if not plan:
        raise ServiceError("Plan not found or inactive.", code="invalid_plan")

    if start_mode == "from_today":
        start = ist_today()
    elif start_mode == "from_previous_end":
        start = previous.end_date + timedelta(days=1)
    elif start_mode == "custom":
        if not custom_start_date:
            raise ServiceError("A custom start date is required.", code="missing_date")
        start = custom_start_date
    else:
        raise ServiceError("Invalid start mode.", code="bad_start_mode")

    _all, active = _active_memberships_locked(member)
    # Block a renewal that would overlap an already-active membership (pre-renewal
    # into an active window is not allowed in v1).
    for m in active:
        if start <= m.end_date:
            raise ServiceError(
                "Renewal would overlap the current active membership; "
                "start it after the current end date.",
                code="renewal_overlap",
            )

    selected = _resolve_addons(gym, addon_ids)
    _subtotal, total = _price_enrollment(plan, selected, [], discount_paise, expected_total_paise)
    amount = total if amount_paid_paise is None else amount_paid_paise
    if amount < 0 or amount > total:
        raise ServiceError("Amount paid must be between 0 and the order total.", code="bad_amount")

    membership, payment = _create_membership_with_payment(
        gym=gym, actor=actor, member=member, plan=plan, selected_addons=selected,
        auto_addons=[], discount_paise=discount_paise, method=method,
        amount_paid_paise=amount, total=total, start_date=start, kind=PaymentKind.RENEWAL,
        previous=previous,
    )
    audit.record(
        actor=actor, action=AuditAction.RENEW, entity=membership,
        after={"plan": plan.name, "total_paise": total, "paid_paise": amount,
               "previous_membership": previous.id},
        summary=f"Renewed into {plan.name}",
    )
    return membership, payment


@transaction.atomic
def correct_membership(*, gym, actor, membership_id, plan_id=None, start_date=None,
                       addon_ids=None, reason=""):
    membership = Membership.objects.select_for_update().filter(gym=gym, id=membership_id).first()
    if not membership:
        raise ServiceError("Membership not found.", code="not_found", status=404)

    allowed, why = can_correct_membership(actor, membership)
    if not allowed:
        raise ServiceError(why, code="correction_not_allowed", status=403)

    before = {
        "plan": membership.plan_name, "start_date": membership.start_date.isoformat(),
        "end_date": membership.end_date.isoformat(),
    }

    if plan_id is not None:
        plan = Plan.objects.filter(gym=gym, id=plan_id).first()
        if not plan:
            raise ServiceError("Plan not found.", code="invalid_plan")
        membership.plan = plan
        membership.plan_name = plan.name
        membership.duration_days = plan.duration_days
        membership.plan_price_paise = plan.price_paise
    if start_date is not None:
        membership.start_date = start_date

    # Recompute end_date from (possibly corrected) start + duration.
    # original_end_date stays pinned (immutable).
    membership.end_date = membership.start_date + timedelta(days=membership.duration_days)

    if addon_ids is not None:
        addons = _resolve_addons(gym, addon_ids)
        membership.addons.all().delete()
        for a in addons:
            MembershipAddOn.objects.create(
                gym=gym, branch=membership.branch, membership=membership, addon=a,
                name=a.name, addon_type=a.addon_type, price_paise=a.price_paise,
            )

    membership.correction_count += 1
    membership.save()

    audit.record(
        actor=actor, action=AuditAction.CORRECT, entity=membership,
        before=before,
        after={"plan": membership.plan_name, "start_date": membership.start_date.isoformat(),
               "end_date": membership.end_date.isoformat(), "reason": reason},
        summary=f"Corrected membership (#{membership.correction_count})",
    )
    return membership


@transaction.atomic
def cancel_membership(*, gym, actor, membership_id, effective_date, prorated_refund=False,
                      method="cash", reason=""):
    from common.dates import ist_now

    membership = Membership.objects.select_for_update().filter(gym=gym, id=membership_id).first()
    if not membership:
        raise ServiceError("Membership not found.", code="not_found", status=404)
    if membership.cancel_effective_date is not None:
        raise ServiceError("Membership is already cancelled.", code="already_cancelled")

    membership.cancelled_at = ist_now()
    membership.cancel_effective_date = effective_date
    membership.cancel_reason = reason
    membership.save(update_fields=[
        "cancelled_at", "cancel_effective_date", "cancel_reason", "updated_at"
    ])

    refund = None
    if prorated_refund:
        net_paid = net_paid_for_membership(membership)
        total_days = (membership.end_date - membership.start_date).days + 1
        remaining_days = max((membership.end_date - effective_date).days + 1, 0)
        if total_days > 0 and remaining_days > 0 and net_paid > 0:
            amount = round(net_paid * remaining_days / total_days)
            amount = min(amount, net_paid)
            if amount > 0:
                last_payment = membership.payments.filter(amount_paise__gt=0).order_by("-created_at").first()
                refund = create_refund(
                    original=last_payment, amount_paise=amount,
                    reason=reason or "Prorated cancellation refund", actor=actor, gym=gym,
                )

    audit.record(
        actor=actor, action=AuditAction.CANCEL, entity=membership,
        after={"effective_date": effective_date.isoformat(),
               "prorated_refund_paise": (-refund.amount_paise if refund else 0), "reason": reason},
        summary="Cancelled membership",
    )
    return membership, refund
