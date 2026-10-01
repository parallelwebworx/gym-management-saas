import threading

import pytest
from django.db import connection, transaction
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import Plan
from members.models import Member
from memberships import services
from payments.models import Payment, allocate_invoice_number, net_paid_for_membership
from tenants.models import Branch, Gym, Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Gym A", invoice_prefix="INV")
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


def test_refund_owner_only_and_caps_at_balance(world):
    m, p = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    paid = net_paid_for_membership(m)

    # receptionist is forbidden
    rc = client_for(world["reception"])
    assert rc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": 1000}, format="json").status_code == 403

    oc = client_for(world["owner"])
    # over-refund rejected
    over = oc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": paid + 1}, format="json")
    assert over.status_code == 400
    # valid partial refund
    ok_resp = oc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": 5000, "reason": "goodwill"}, format="json")
    assert ok_resp.status_code == 201, ok_resp.content
    refund = ok_resp.json()["data"]["refund"]
    assert refund["amount_paise"] == -5000
    assert net_paid_for_membership(m) == paid - 5000


def test_cannot_refund_more_after_partial(world):
    m, p = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    paid = net_paid_for_membership(m)
    oc = client_for(world["owner"])
    oc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": paid - 1000}, format="json")
    # only 1000 remains
    too_much = oc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": 2000}, format="json")
    assert too_much.status_code == 400


def test_edit_payment_requires_reason_and_keeps_trail(world):
    m, p = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    oc = client_for(world["owner"])
    assert oc.post(f"/api/payments/{p.id}/edit/", {"amount_paise": 100000}, format="json").status_code == 400  # no reason
    resp = oc.post(f"/api/payments/{p.id}/edit/", {"amount_paise": 100000, "reason": "cash miscount"}, format="json")
    assert resp.status_code == 200, resp.content
    p.refresh_from_db()
    assert p.edited is True
    assert p.original_amount_paise == 150000  # plan price (no auto add-on in this fixture)
    assert p.amount_paise == 100000


def test_ledger_net_revenue_and_filters(world):
    m, p = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    oc = client_for(world["owner"])
    oc.post(f"/api/payments/{p.id}/refund/", {"amount_paise": 5000}, format="json")
    # ledger lists both payment + refund
    lst = oc.get("/api/payments/").json()["data"]
    assert lst["count"] == 2
    refunds = oc.get("/api/payments/?kind=refund").json()["data"]
    assert refunds["count"] == 1


def test_payment_sign_constraint_blocks_bad_row(world):
    """DB CheckConstraint: a non-refund payment cannot be negative."""
    from django.db.utils import IntegrityError
    m, _ = services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    with pytest.raises(IntegrityError):
        Payment.objects.create(
            gym=world["gym"], branch=world["branch"], member=world["member"], membership=m,
            kind="enrollment", amount_paise=-999, invoice_number="BAD-1",
        )


def test_cross_gym_cannot_see_payments(world):
    services.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    other_gym = Gym.objects.create(name="Gym B")
    ob = Branch.objects.create(gym=other_gym, name="Main Branch")
    other_owner = User.objects.create_user(email="o@b.com", password="pw-123456aa", role=Role.OWNER, gym=other_gym, branch=ob)
    assert client_for(other_owner).get("/api/payments/").json()["data"]["count"] == 0


@pytest.mark.django_db(transaction=True)
def test_invoice_numbers_unique_under_concurrency():
    """Concurrent allocations must never collide (row-locked counter)."""
    gym = Gym.objects.create(name="Conc Gym", invoice_prefix="CON")
    results = []
    errors = []
    N = 20

    def allocate_one():
        try:
            with transaction.atomic():
                results.append(allocate_invoice_number(gym))
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))
        finally:
            connection.close()

    threads = [threading.Thread(target=allocate_one) for _ in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    assert len(results) == N
    assert len(set(results)) == N  # all unique
    seqs = sorted(int(r.split("-")[-1]) for r in results)
    assert seqs == list(range(1, N + 1))  # contiguous 1..N
