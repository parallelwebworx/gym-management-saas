from datetime import timedelta

import pytest

from catalogue.models import Plan
from common.dates import ist_today
from common.errors import ServiceError
from members.models import Member
from memberships import services
from memberships.models import MembershipStatus
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Gym A", invoice_prefix="IRN")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    member = Member.objects.create(gym=gym, branch=branch, full_name="Asha", phone="+919876543210")
    return locals()


def _enroll(world):
    m, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    return m


def test_freeze_sets_frozen_status(world):
    m = _enroll(world)
    m2, freeze = services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id)
    assert m2.status == MembershipStatus.FROZEN
    assert freeze.freeze_end_date is None
    assert freeze.completed is False


def test_unfreeze_extends_end_date_day_accurate(world):
    m = _enroll(world)
    original_end = m.end_date
    start = ist_today() - timedelta(days=5)  # froze 5 days ago
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, start_date=start)
    # unfreeze as of today -> 5 frozen days
    m2, freeze = services.unfreeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, end_date=ist_today())
    assert freeze.days_added == 5
    assert m2.end_date == original_end + timedelta(days=5)
    assert m2.status == MembershipStatus.ACTIVE


def test_sum_days_added_equals_total_extension(world):
    m = _enroll(world)
    original_end = m.original_end_date
    start = ist_today()
    # First freeze: 3 days
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, start_date=start)
    services.unfreeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, end_date=start + timedelta(days=3))
    # Second freeze: 4 days
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, start_date=start + timedelta(days=10))
    m2, _ = services.unfreeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, end_date=start + timedelta(days=14))
    total_added = sum(f.days_added for f in m2.freezes.all())
    assert total_added == 7
    assert (m2.end_date - original_end).days == total_added  # Σ invariant


def test_cannot_double_freeze(world):
    m = _enroll(world)
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id)
    with pytest.raises(ServiceError) as exc:
        services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id)
    assert exc.value.code == "already_frozen"


def test_frozen_membership_blocks_new_enrollment(world):
    m = _enroll(world)
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id)
    with pytest.raises(ServiceError) as exc:
        services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    assert exc.value.code == "member_has_active_membership"


def test_cannot_unfreeze_when_not_frozen(world):
    m = _enroll(world)
    with pytest.raises(ServiceError) as exc:
        services.unfreeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id)
    assert exc.value.code == "not_frozen"


def test_correction_preserves_frozen_days(world):
    m = _enroll(world)
    start = ist_today()
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, start_date=start)
    m2, _ = services.unfreeze_membership(gym=world["gym"], actor=world["owner"], membership_id=m.id, end_date=start + timedelta(days=6))
    # Correct the start date; the 6 frozen days must still be reflected.
    corrected = services.correct_membership(
        gym=world["gym"], actor=world["owner"], membership_id=m.id,
        start_date=m2.start_date, reason="fix",
    )
    assert (corrected.end_date - corrected.start_date).days == corrected.duration_days + 6
