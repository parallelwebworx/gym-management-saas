import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import Plan
from common.money import rupees_in_words
from members.models import Member
from memberships import services as mservices
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Iron Paradise", invoice_prefix="IRN", gstin="29ABCDE1234F1Z5")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    member = Member.objects.create(gym=gym, branch=branch, full_name="Asha Rao", phone="+919876543210")
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_tax_invoice_pdf(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    resp = client_for(world["owner"]).get(f"/api/invoices/{p.id}/pdf/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
    assert "IRN-" in resp["Content-Disposition"]


def test_receipt_when_no_gstin(world):
    world["gym"].gstin = ""
    world["gym"].save()
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    resp = client_for(world["owner"]).get(f"/api/invoices/{p.id}/pdf/")
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_invoice_pdf_gym_isolated(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    other = Gym.objects.create(name="Gym B")
    ob = Branch.objects.create(gym=other, name="Main Branch")
    oo = User.objects.create_user(email="o@b.com", password="pw-123456aa", role=Role.OWNER, gym=other, branch=ob)
    assert client_for(oo).get(f"/api/invoices/{p.id}/pdf/").status_code == 404


def test_rupees_in_words():
    assert rupees_in_words(150000) == "One Thousand Five Hundred Rupees Only"
    assert rupees_in_words(200000) == "Two Thousand Rupees Only"
    assert rupees_in_words(10050) == "One Hundred Rupees and Fifty Paise Only"
