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
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch, full_name="Owner O")
    reception = User.objects.create_user(email="r@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch, full_name="Rec R")
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def _member(world, name, phone):
    return Member.objects.create(gym=world["gym"], branch=world["branch"], full_name=name, phone=phone)


def test_overview_totals_and_discount(world):
    # Two enrollments, one with a 50k discount.
    m1 = _member(world, "A", "+919800000001")
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=m1.id, plan_id=world["plan"].id)
    m2 = _member(world, "B", "+919800000002")
    mservices.enroll(gym=world["gym"], actor=world["reception"], member_id=m2.id, plan_id=world["plan"].id, discount_paise=50000)

    data = client_for(world["owner"]).get("/api/reports/overview/").json()["data"]
    ov = data["overview"]
    assert ov["gross_paise"] == 150000 + 100000  # second paid 100000 after discount
    assert ov["discount_paise"] == 50000
    assert ov["enrollments"] == 2
    assert ov["discount_rate_pct"] >= 15
    # trend has an entry per day and ends at cumulative == net
    assert data["trend"][-1]["cumulative_paise"] == ov["net_paise"]
    # high discount rate anomaly present
    assert any(a["code"] == "high_discount_rate" for a in data["anomalies"])


def test_discount_leakage_by_staff(world):
    m1 = _member(world, "A", "+919800000001")
    mservices.enroll(gym=world["gym"], actor=world["reception"], member_id=m1.id, plan_id=world["plan"].id, discount_paise=30000)
    m2 = _member(world, "B", "+919800000002")
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=m2.id, plan_id=world["plan"].id, discount_paise=0)

    staff = client_for(world["owner"]).get("/api/reports/discounts/").json()["data"]["staff"]
    by_name = {s["staff_name"]: s for s in staff}
    assert by_name["Rec R"]["total_discount_paise"] == 30000
    assert by_name["Owner O"]["total_discount_paise"] == 0


def test_plan_sales(world):
    m1 = _member(world, "A", "+919800000001")
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=m1.id, plan_id=world["plan"].id)
    plans = client_for(world["owner"]).get("/api/reports/plans/").json()["data"]["plans"]
    assert plans[0]["plan_name"] == "Monthly"
    assert plans[0]["count"] == 1


def test_reports_forbidden_for_receptionist(world):
    assert client_for(world["reception"]).get("/api/reports/overview/").status_code == 403


def test_revenue_xlsx_export(world):
    resp = client_for(world["owner"]).get("/api/reports/revenue/?export=xlsx")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("application/vnd.openxmlformats")


def test_reports_are_gym_isolated(world):
    m1 = _member(world, "A", "+919800000001")
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=m1.id, plan_id=world["plan"].id)
    other = Gym.objects.create(name="Gym B")
    ob = Branch.objects.create(gym=other, name="Main Branch")
    oo = User.objects.create_user(email="o@b.com", password="pw-123456aa", role=Role.OWNER, gym=other, branch=ob)
    ov = client_for(oo).get("/api/reports/overview/").json()["data"]["overview"]
    assert ov["net_paise"] == 0
