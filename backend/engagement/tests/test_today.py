from datetime import timedelta

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import Plan
from common.dates import ist_today
from members.models import Member
from memberships import services
from memberships.models import Membership
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Gym A", invoice_prefix="IRN")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def _member(world, name, phone):
    return Member.objects.create(gym=world["gym"], branch=world["branch"], full_name=name, phone=phone)


def test_today_metrics_and_lists(world):
    today = ist_today()
    # Enroll today -> revenue + new enrollment + expiring (30d > 14 so NOT expiring_soon)
    m1 = _member(world, "Fresh Today", "+919800000001")
    services.enroll(gym=world["gym"], actor=world["owner"], member_id=m1.id, plan_id=world["plan"].id)

    # An expiring-soon membership (ends in 3 days)
    m2 = _member(world, "Expiring Soon", "+919800000002")
    mem2, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=m2.id, plan_id=world["plan"].id)
    Membership.objects.filter(pk=mem2.pk).update(end_date=today + timedelta(days=3))

    # A recently-expired membership (ended 2 days ago)
    m3 = _member(world, "Recently Expired", "+919800000003")
    mem3, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=m3.id, plan_id=world["plan"].id)
    Membership.objects.filter(pk=mem3.pk).update(end_date=today - timedelta(days=2))

    # A frozen membership
    m4 = _member(world, "Frozen Guy", "+919800000004")
    mem4, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=m4.id, plan_id=world["plan"].id)
    services.freeze_membership(gym=world["gym"], actor=world["owner"], membership_id=mem4.id)

    data = client_for(world["owner"]).get("/api/today/").json()["data"]
    metrics = data["metrics"]

    assert metrics["new_enrollments_today"] == 4
    assert metrics["revenue_today_paise"] == 4 * 150000
    assert metrics["frozen_now"] == 1
    assert metrics["expiring_3d"] >= 1

    expiring_names = {r["member_name"] for r in data["expiring_soon"]}
    assert "Expiring Soon" in expiring_names
    assert "Frozen Guy" not in expiring_names  # frozen != expiring

    recent_names = {r["member_name"] for r in data["recently_expired"]}
    assert "Recently Expired" in recent_names


def test_log_reminder_shows_on_today(world):
    today = ist_today()
    m = _member(world, "Call Me", "+919800000009")
    mem, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=m.id, plan_id=world["plan"].id)
    Membership.objects.filter(pk=mem.pk).update(end_date=today + timedelta(days=2))
    c = client_for(world["owner"])

    created = c.post("/api/reminders/", {"member": m.id, "membership": mem.id, "channel": "whatsapp"}, format="json")
    assert created.status_code == 201, created.content

    data = c.get("/api/today/").json()["data"]
    row = next(r for r in data["expiring_soon"] if r["member_id"] == m.id)
    assert row["last_reminded_at"] is not None


def test_today_is_branch_scoped(world):
    # A second branch with its own expiring member; a branch_manager must not see it.
    other_branch = Branch.objects.create(gym=world["gym"], name="Second Branch")
    today = ist_today()
    m = _member(world, "Main Expiring", "+919800000011")
    mem, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=m.id, plan_id=world["plan"].id)
    Membership.objects.filter(pk=mem.pk).update(end_date=today + timedelta(days=2))

    mgr = User.objects.create_user(email="mgr@a.com", password="pw-123456aa", role=Role.BRANCH_MANAGER, gym=world["gym"], branch=other_branch)
    data = client_for(mgr).get("/api/today/").json()["data"]
    assert all(r["member_name"] != "Main Expiring" for r in data["expiring_soon"])
