import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import AddOn, Plan
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def gym_setup():
    gym = Gym.objects.create(name="Gym A")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(
        email="owner@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch
    )
    reception = User.objects.create_user(
        email="front@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch
    )
    return {"gym": gym, "branch": branch, "owner": owner, "reception": reception}


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_owner_creates_plan(gym_setup):
    c = client_for(gym_setup["owner"])
    resp = c.post("/api/plans/", {
        "name": "Monthly", "plan_type": "general", "duration_days": 30, "price_paise": 150000,
    }, format="json")
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["name"] == "Monthly"
    assert Plan.objects.filter(gym=gym_setup["gym"]).count() == 1


def test_receptionist_cannot_write_plan(gym_setup):
    c = client_for(gym_setup["reception"])
    resp = c.post("/api/plans/", {
        "name": "Monthly", "plan_type": "general", "duration_days": 30, "price_paise": 150000,
    }, format="json")
    assert resp.status_code == 403


def test_receptionist_can_read_plans(gym_setup):
    Plan.objects.create(gym=gym_setup["gym"], name="Monthly", duration_days=30, price_paise=150000)
    c = client_for(gym_setup["reception"])
    resp = c.get("/api/plans/")
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 1


def test_plan_name_ci_unique_per_gym(gym_setup):
    c = client_for(gym_setup["owner"])
    payload = {"name": "Monthly", "plan_type": "general", "duration_days": 30, "price_paise": 1000}
    assert c.post("/api/plans/", payload, format="json").status_code == 201
    dup = c.post("/api/plans/", {**payload, "name": "MONTHLY"}, format="json")
    assert dup.status_code == 400
    assert "already exists" in str(dup.content).lower()


def test_addon_auto_apply_flag(gym_setup):
    c = client_for(gym_setup["owner"])
    resp = c.post("/api/add-ons/", {
        "name": "Joining Fee", "addon_type": "one_time", "price_paise": 50000,
        "auto_apply_on_first_enrollment": True,
    }, format="json")
    assert resp.status_code == 201
    assert AddOn.objects.get(gym=gym_setup["gym"]).auto_apply_on_first_enrollment is True


def test_plans_are_gym_isolated(gym_setup):
    other = Gym.objects.create(name="Gym B")
    Plan.objects.create(gym=other, name="Other Plan", duration_days=30, price_paise=1000)
    Plan.objects.create(gym=gym_setup["gym"], name="My Plan", duration_days=30, price_paise=1000)
    c = client_for(gym_setup["owner"])
    resp = c.get("/api/plans/")
    names = {p["name"] for p in resp.json()["data"]["results"]}
    assert names == {"My Plan"}
