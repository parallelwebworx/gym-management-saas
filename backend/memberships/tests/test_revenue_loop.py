from datetime import timedelta

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from audit.models import AuditLog
from catalogue.models import AddOn, Plan
from common.dates import ist_today
from members.models import Member
from memberships import services
from memberships.models import Membership, MembershipStatus
from payments.models import net_paid_for_membership
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Gym A", invoice_prefix="IRN")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    reception = User.objects.create_user(email="r@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    joining = AddOn.objects.create(gym=gym, name="Joining Fee", addon_type="one_time", price_paise=50000, auto_apply_on_first_enrollment=True)
    locker = AddOn.objects.create(gym=gym, name="Locker", addon_type="recurring", price_paise=20000)
    member = Member.objects.create(gym=gym, branch=branch, full_name="Asha Rao", phone="+919876543210")
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


# -- enrollment ----------------------------------------------------------
def test_enroll_auto_applies_joining_fee_and_computes_total(world):
    m, p = services.enroll(
        gym=world["gym"], actor=world["owner"], member_id=world["member"].id,
        plan_id=world["plan"].id, addon_ids=[world["locker"].id], discount_paise=10000,
    )
    # 150000 + 20000 (locker) + 50000 (auto joining) - 10000 discount = 210000
    assert net_paid_for_membership(m) == 210000
    assert p.amount_paise == 210000
    assert p.invoice_number == f"IRN-{ist_today().year}-0001"
    assert m.addons.count() == 2  # locker + auto joining
    assert m.status == MembershipStatus.ACTIVE
    assert m.end_date == m.start_date + timedelta(days=30)
    assert m.original_end_date == m.end_date


def test_enroll_rejects_tampered_total(world):
    from common.errors import ServiceError
    with pytest.raises(ServiceError) as exc:
        services.enroll(
            gym=world["gym"], actor=world["owner"], member_id=world["member"].id,
            plan_id=world["plan"].id, addon_ids=[], discount_paise=0,
            expected_total_paise=1,  # wrong on purpose
        )
    assert exc.value.code == "amount_mismatch"


def test_enroll_blocks_second_active_membership(world):
    from common.errors import ServiceError
    services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    with pytest.raises(ServiceError) as exc:
        services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    assert exc.value.code == "member_has_active_membership"


def test_enroll_writes_audit_row(world):
    services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    assert AuditLog.objects.filter(action="enroll", gym=world["gym"]).count() == 1


def test_enroll_via_api_combined_add_member(world):
    c = client_for(world["reception"])
    resp = c.post("/api/memberships/enroll/", {
        "member": {"full_name": "New Guy", "phone": "9811112222"},
        "plan_id": world["plan"].id,
    }, format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()["data"]
    assert data["membership"]["member_name"] == "New Guy"
    assert Member.objects.filter(gym=world["gym"], full_name="New Guy").exists()


# -- renewal -------------------------------------------------------------
def test_renew_from_previous_end_increments_invoice(world):
    m1, p1 = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    m2, p2 = services.renew(
        gym=world["gym"], actor=world["owner"], membership_id=m1.id,
        plan_id=world["plan"].id, start_mode="from_previous_end",
    )
    assert m2.start_date == m1.end_date + timedelta(days=1)
    assert m2.previous_id == m1.id
    assert p2.invoice_number.endswith("0002")
    assert p2.kind == "renewal"


def test_renew_from_today_blocks_overlap_with_active(world):
    from common.errors import ServiceError
    m1, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    with pytest.raises(ServiceError) as exc:
        services.renew(gym=world["gym"], actor=world["owner"], membership_id=m1.id, plan_id=world["plan"].id, start_mode="from_today")
    assert exc.value.code == "renewal_overlap"


# -- correction matrix ---------------------------------------------------
def test_owner_can_correct_within_90_days_and_pins_original_end(world):
    m, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    original_end = m.original_end_date
    long_plan = Plan.objects.create(gym=world["gym"], name="Quarterly", duration_days=90, price_paise=400000)
    corrected = services.correct_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, plan_id=long_plan.id, reason="wrong plan")
    assert corrected.duration_days == 90
    assert corrected.end_date == corrected.start_date + timedelta(days=90)
    assert corrected.original_end_date == original_end  # immutable
    assert corrected.correction_count == 1


def test_receptionist_correction_blocked_after_window(world):
    from common.errors import ServiceError
    m, _ = services.enroll(gym=world["gym"], actor=world["reception"], member_id=world["member"].id, plan_id=world["plan"].id)
    # Force created_at into the past (beyond 60 min).
    Membership.objects.filter(pk=m.pk).update(created_at=m.created_at - timedelta(hours=2))
    m.refresh_from_db()
    with pytest.raises(ServiceError) as exc:
        services.correct_membership(gym=world["gym"], actor=world["reception"], membership_id=m.id, start_date=ist_today())
    assert exc.value.code == "correction_not_allowed"


def test_receptionist_can_correct_own_within_window(world):
    m, _ = services.enroll(gym=world["gym"], actor=world["reception"], member_id=world["member"].id, plan_id=world["plan"].id)
    corrected = services.correct_membership(gym=world["gym"], actor=world["reception"], membership_id=m.id, start_date=ist_today())
    assert corrected.correction_count == 1


# -- cancellation --------------------------------------------------------
def test_cancel_sets_status_and_prorated_refund(world):
    m, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id, addon_ids=[])
    # paid 200000 (150000 plan + 50000 auto joining), 31 days total (incl.)
    net_before = net_paid_for_membership(m)
    effective = m.start_date  # cancel from day one -> full remaining
    m2, refund = services.cancel_membership(
        gym=world["gym"], actor=world["owner"], membership_id=m.id,
        effective_date=effective, prorated_refund=True, reason="moved city",
    )
    assert m2.status_on(effective) == MembershipStatus.CANCELLED
    assert refund is not None
    assert refund.amount_paise < 0
    # Refunding from the start returns (almost) the whole amount.
    assert -refund.amount_paise <= net_before
    assert net_paid_for_membership(m) == net_before + refund.amount_paise


def test_cancel_is_owner_only_via_api(world):
    m, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    c = client_for(world["reception"])
    resp = c.post(f"/api/memberships/{m.id}/cancel/", {"effective_date": str(ist_today())}, format="json")
    assert resp.status_code == 403


# -- isolation -----------------------------------------------------------
def test_cross_gym_cannot_enroll(world):
    from common.errors import ServiceError
    other_gym = Gym.objects.create(name="Gym B")
    with pytest.raises(ServiceError) as exc:
        services.enroll(gym=other_gym, actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    assert exc.value.code == "not_found"  # member belongs to Gym A
