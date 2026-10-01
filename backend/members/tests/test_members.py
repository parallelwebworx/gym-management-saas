import io

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from members.models import Member
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup():
    gym = Gym.objects.create(name="Gym A")
    other = Gym.objects.create(name="Gym B")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    other_branch = Branch.objects.create(gym=other, name="Main Branch")
    owner = User.objects.create_user(
        email="owner@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch
    )
    reception = User.objects.create_user(
        email="front@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch
    )
    other_owner = User.objects.create_user(
        email="owner@b.com", password="pw-123456aa", role=Role.OWNER, gym=other, branch=other_branch
    )
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_create_member_normalizes_phone(setup):
    c = client_for(setup["owner"])
    resp = c.post("/api/members/", {"full_name": "Asha Rao", "phone": "9876543210"}, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.json()["data"]["phone"] == "+919876543210"
    m = Member.objects.get(gym=setup["gym"])
    assert m.branch_id == setup["branch"].id  # stamped from request


def test_invalid_phone_rejected(setup):
    c = client_for(setup["owner"])
    resp = c.post("/api/members/", {"full_name": "X", "phone": "12345"}, format="json")
    assert resp.status_code == 400


def test_duplicate_phone_rejected(setup):
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="A", phone="+919876543210")
    c = client_for(setup["owner"])
    resp = c.post("/api/members/", {"full_name": "B", "phone": "9876543210"}, format="json")
    assert resp.status_code == 400
    assert "already exists" in str(resp.content).lower()


def test_check_phone_endpoint(setup):
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="A", phone="+919876543210")
    c = client_for(setup["owner"])
    resp = c.get("/api/members/check-phone/?phone=98765 43210")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["exists"] is True and data["member"]["full_name"] == "A"
    resp2 = c.get("/api/members/check-phone/?phone=9000000000")
    assert resp2.json()["data"]["exists"] is False


def test_search_finds_member(setup):
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="Asha Rao", phone="+919876543210")
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="Bhanu Singh", phone="+919812345678")
    c = client_for(setup["owner"])
    by_name = c.get("/api/members/?search=asha")
    names = [m["full_name"] for m in by_name.json()["data"]["results"]]
    assert "Asha Rao" in names
    by_phone = c.get("/api/members/?search=9812")
    phones = [m["phone"] for m in by_phone.json()["data"]["results"]]
    assert "+919812345678" in phones


def test_members_gym_isolated(setup):
    Member.objects.create(gym=setup["other"], branch=setup["other_branch"], full_name="Foreign", phone="+919000000000")
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="Mine", phone="+919876543210")
    c = client_for(setup["owner"])
    names = {m["full_name"] for m in c.get("/api/members/").json()["data"]["results"]}
    assert names == {"Mine"}


def test_receptionist_cannot_delete(setup):
    m = Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="A", phone="+919876543210")
    c = client_for(setup["reception"])
    assert c.delete(f"/api/members/{m.id}/").status_code == 403


def test_owner_soft_delete_and_restore(setup):
    m = Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="A", phone="+919876543210")
    c = client_for(setup["owner"])
    assert c.delete(f"/api/members/{m.id}/").status_code == 204
    m.refresh_from_db()
    assert m.deleted_at is not None
    assert Member.objects.filter(pk=m.pk).count() == 0  # hidden by manager
    resp = c.post(f"/api/members/{m.id}/restore/")
    assert resp.status_code == 200
    assert Member.objects.filter(pk=m.pk).count() == 1


def test_csv_import_preview_and_commit(setup):
    csv_content = (
        "full_name,phone,email,gender\n"
        "Asha Rao,9876543210,asha@example.com,female\n"
        "Bad Row,12345,,\n"
        "Asha Rao,9876543210,,female\n"  # dup within file
    )
    c = client_for(setup["owner"])
    # preview (commit=false)
    preview = c.post("/api/members/import/", {"file": io.BytesIO(csv_content.encode())}, format="multipart")
    assert preview.status_code == 200, preview.content
    pdata = preview.json()["data"]
    assert pdata["committed"] is False
    assert pdata["summary"]["valid"] == 1
    assert pdata["summary"]["errors"] == 1
    assert pdata["summary"]["duplicates"] == 1
    assert Member.objects.filter(gym=setup["gym"]).count() == 0  # nothing written on preview
    # commit
    commit = c.post("/api/members/import/?commit=true", {"file": io.BytesIO(csv_content.encode())}, format="multipart")
    cdata = commit.json()["data"]
    assert cdata["inserted"] == 1
    assert Member.objects.filter(gym=setup["gym"]).count() == 1


def test_excel_export(setup):
    Member.objects.create(gym=setup["gym"], branch=setup["branch"], full_name="A", phone="+919876543210")
    c = client_for(setup["owner"])
    resp = c.get("/api/members/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("application/vnd.openxmlformats")
    assert resp["Content-Disposition"].endswith('members.xlsx"')
    assert len(resp.content) > 0
