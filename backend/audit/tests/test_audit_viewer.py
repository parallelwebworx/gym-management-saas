import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import Plan
from members.models import Member
from memberships import services as mservices
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Gym A", invoice_prefix="IRN")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    reception = User.objects.create_user(email="r@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    member = Member.objects.create(gym=gym, branch=branch, full_name="Asha", phone="+919876543210")
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_enroll_appears_in_audit_viewer(world):
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    data = client_for(world["owner"]).get("/api/audit-logs/").json()["data"]
    assert data["count"] >= 1
    actions = {r["action"] for r in data["results"]}
    assert "enroll" in actions


def test_audit_filter_by_action_and_before_after(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    client_for(world["owner"]).post(f"/api/payments/{p.id}/edit/", {"amount_paise": 100000, "reason": "fix"}, format="json")
    rows = client_for(world["owner"]).get("/api/audit-logs/?action=edit_payment").json()["data"]["results"]
    assert len(rows) == 1
    assert rows[0]["before"]["amount_paise"] == 150000  # original enrollment amount
    assert rows[0]["after"]["amount_paise"] == 100000


def test_refund_is_audited(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    client_for(world["owner"]).post(f"/api/payments/{p.id}/refund/", {"amount_paise": 5000, "reason": "goodwill"}, format="json")
    rows = client_for(world["owner"]).get("/api/audit-logs/?action=refund").json()["data"]["results"]
    assert len(rows) == 1
    assert rows[0]["after"]["amount_paise"] == -5000


def test_audit_forbidden_for_receptionist(world):
    assert client_for(world["reception"]).get("/api/audit-logs/").status_code == 403


def test_audit_export_xlsx(world):
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    resp = client_for(world["owner"]).get("/api/audit-logs/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("application/vnd.openxmlformats")


def test_audit_is_gym_isolated(world):
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    other = Gym.objects.create(name="Gym B")
    ob = Branch.objects.create(gym=other, name="Main Branch")
    oo = User.objects.create_user(email="o@b.com", password="pw-123456aa", role=Role.OWNER, gym=other, branch=ob)
    assert client_for(oo).get("/api/audit-logs/").json()["data"]["count"] == 0
