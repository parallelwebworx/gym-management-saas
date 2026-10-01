"""
Phase-0 tenant-isolation smoke test (mirrors the source app's test-rls.ts intent).

Two gyms are provisioned; we assert that a user authenticated into gym A cannot
see gym B's data and vice versa. As more business models arrive, extend the
per-model assertions here — every phase's DoD requires this test to pass.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def two_gyms():
    gym_a = Gym.objects.create(name="Gym A")
    gym_b = Gym.objects.create(name="Gym B")
    branch_a = Branch.objects.create(gym=gym_a, name="Main Branch")
    branch_b = Branch.objects.create(gym=gym_b, name="Main Branch")
    owner_a = User.objects.create_user(
        email="a@example.com", password="pw-aaaaaa1", role=Role.OWNER,
        gym=gym_a, branch=branch_a,
    )
    owner_b = User.objects.create_user(
        email="b@example.com", password="pw-bbbbbb1", role=Role.OWNER,
        gym=gym_b, branch=branch_b,
    )
    return {
        "gym_a": gym_a, "gym_b": gym_b,
        "branch_a": branch_a, "branch_b": branch_b,
        "owner_a": owner_a, "owner_b": owner_b,
    }


def _auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def test_login_returns_tokens_and_user(two_gyms):
    client = APIClient()
    resp = client.post(
        reverse("auth-login"),
        {"email": "a@example.com", "password": "pw-aaaaaa1"},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "access" in body["data"] and "refresh" in body["data"]
    assert body["data"]["user"]["gym"]["name"] == "Gym A"


def test_login_rejects_bad_password(two_gyms):
    client = APIClient()
    resp = client.post(
        reverse("auth-login"),
        {"email": "a@example.com", "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 401
    assert resp.json()["ok"] is False


def test_branches_are_gym_scoped(two_gyms):
    """Owner A sees only gym A's branch; never gym B's."""
    client = _auth_client(two_gyms["owner_a"])
    resp = client.get(reverse("branch-list"))
    assert resp.status_code == 200
    data = resp.json()["data"]["results"]
    ids = {b["id"] for b in data}
    assert two_gyms["branch_a"].id in ids
    assert two_gyms["branch_b"].id not in ids  # cross-tenant read = 0


def test_me_reflects_authenticated_tenant(two_gyms):
    client = _auth_client(two_gyms["owner_b"])
    resp = client.get(reverse("auth-me"))
    assert resp.status_code == 200
    assert resp.json()["data"]["gym"]["name"] == "Gym B"


def test_unauthenticated_is_rejected(two_gyms):
    resp = APIClient().get(reverse("branch-list"))
    assert resp.status_code == 401
