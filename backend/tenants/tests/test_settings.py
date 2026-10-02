import time

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from members.models import Member
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Iron Paradise", invoice_prefix="IRN")
    main = Branch.objects.create(gym=gym, name="Main Branch")
    second = Branch.objects.create(gym=gym, name="MG Road")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=main)
    reception = User.objects.create_user(email="r@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=main)
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_owner_updates_gym_profile(world):
    resp = client_for(world["owner"]).patch("/api/settings/gym/", {"gstin": "29abcde1234f1z5", "invoice_prefix": "GYM"}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["data"]["gstin"] == "29ABCDE1234F1Z5"  # upper-cased
    world["gym"].refresh_from_db()
    assert world["gym"].invoice_prefix == "GYM"


def test_receptionist_cannot_edit_gym(world):
    assert client_for(world["reception"]).patch("/api/settings/gym/", {"name": "Hacked"}, format="json").status_code == 403


def test_gstin_length_validated(world):
    assert client_for(world["owner"]).patch("/api/settings/gym/", {"gstin": "short"}, format="json").status_code == 400


def test_create_and_rename_branch(world):
    created = client_for(world["owner"]).post("/api/branches/", {"name": "Baner"}, format="json")
    assert created.status_code == 201, created.content
    bid = created.json()["data"]["id"]
    renamed = client_for(world["owner"]).patch(f"/api/branches/{bid}/", {"name": "Baner West"}, format="json")
    assert renamed.json()["data"]["name"] == "Baner West"


def test_cannot_deactivate_branch_with_members(world):
    Member.objects.create(gym=world["gym"], branch=world["second"], full_name="X", phone="+919876543210")
    resp = client_for(world["owner"]).patch(f"/api/branches/{world['second'].id}/", {"is_active": False}, format="json")
    assert resp.status_code == 409
    assert "members" in resp.json()["error"].lower()


def test_cannot_deactivate_last_branch(world):
    # Deactivate the second (empty) branch first — leaves Main as the only active one.
    world["second"].is_active = False
    world["second"].save()
    resp = client_for(world["owner"]).patch(f"/api/branches/{world['main'].id}/", {"is_active": False}, format="json")
    assert resp.status_code == 409
    assert "last active branch" in resp.json()["error"].lower()


def test_change_password_flow(world):
    c = client_for(world["owner"])
    bad = c.post("/api/settings/password/", {"current_password": "wrong", "new_password": "newpass1234"}, format="json")
    assert bad.status_code == 400
    ok_resp = c.post("/api/settings/password/", {"current_password": "pw-123456aa", "new_password": "newpass1234"}, format="json")
    assert ok_resp.status_code == 200
    world["owner"].refresh_from_db()
    assert world["owner"].check_password("newpass1234")


def test_subscription_view(world):
    data = client_for(world["owner"]).get("/api/settings/subscription/").json()["data"]
    assert data["tier"] == "basic"
    assert data["whatsapp_enabled"] is False


def test_data_export_multisheet(world):
    resp = client_for(world["owner"]).get("/api/settings/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("application/vnd.openxmlformats")
    # Quick sanity: the xlsx is a zip (PK header) and non-trivial.
    assert resp.content[:2] == b"PK"
    assert len(resp.content) > 2000


def test_export_owner_only(world):
    assert client_for(world["reception"]).get("/api/settings/export/").status_code == 403


@pytest.mark.django_db(transaction=True)
def test_member_search_perf_on_large_dataset():
    """Trigram search over ~5k members should stay responsive."""
    gym = Gym.objects.create(name="Big Gym", invoice_prefix="BIG")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="big@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    Member.objects.bulk_create([
        Member(gym=gym, branch=branch, full_name=f"Member {i:05d}", phone=f"+9199{i:08d}")
        for i in range(5000)
    ])
    c = client_for(owner)
    start = time.perf_counter()
    resp = c.get("/api/members/?search=Member 04242")
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] >= 1
    assert elapsed < 2.0  # generous CI budget; target is well under 200ms
