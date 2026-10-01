import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalogue.models import Plan
from members.models import Member
from memberships import services as mservices
from notifications.models import Notification, NotificationStatus
from notifications.providers import ProviderError
from notifications.service import attempt_send
from tenants.models import Branch, Gym, Role, SubscriptionTier, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    gym = Gym.objects.create(name="Iron Paradise", invoice_prefix="IRN")
    branch = Branch.objects.create(gym=gym, name="Main Branch")
    owner = User.objects.create_user(email="o@a.com", password="pw-123456aa", role=Role.OWNER, gym=gym, branch=branch)
    reception = User.objects.create_user(email="r@a.com", password="pw-123456aa", role=Role.RECEPTIONIST, gym=gym, branch=branch)
    plan = Plan.objects.create(gym=gym, name="Monthly", duration_days=30, price_paise=150000)
    member = Member.objects.create(gym=gym, branch=branch, full_name="Asha Rao", phone="+919876543210")
    return locals()


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


def test_enroll_creates_pending_notification(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = Notification.objects.get(membership=m, event="enrollment")
    assert note.status == NotificationStatus.PENDING  # delivery deferred to on_commit
    assert "Iron Paradise" in note.body
    assert note.to_phone == "+919876543210"
    assert note.channel == "sms"  # Basic tier -> SMS


def test_attempt_send_marks_sent_with_stub(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = Notification.objects.get(membership=m)
    assert attempt_send(note) is True
    note.refresh_from_db()
    assert note.status == NotificationStatus.SENT
    assert note.attempts == 1
    assert note.provider_message_id


def test_attempt_send_failure_records_and_raises(world, monkeypatch):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = Notification.objects.get(membership=m)

    class Boom:
        def send(self, *a, **k):
            raise ProviderError("provider down")

    monkeypatch.setattr("notifications.service.get_provider", lambda: Boom())
    with pytest.raises(ProviderError):
        attempt_send(note)
    note.refresh_from_db()
    assert note.status == NotificationStatus.FAILED
    assert note.attempts == 1
    assert "provider down" in note.error


def test_whatsapp_downgrades_to_sms_on_basic_tier(world):
    from notifications.models import NotificationChannel, NotificationEvent
    from notifications.service import queue_notification
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = queue_notification(gym=world["gym"], event=NotificationEvent.RENEWAL,
                              membership=m, payment=p, channel=NotificationChannel.WHATSAPP)
    assert note.channel == "sms"


def test_whatsapp_allowed_on_pro_tier(world):
    from notifications.models import NotificationChannel, NotificationEvent
    from notifications.service import queue_notification
    world["gym"].subscription_tier = SubscriptionTier.PRO
    world["gym"].save()
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = queue_notification(gym=world["gym"], event=NotificationEvent.RENEWAL,
                              membership=m, payment=p, channel=NotificationChannel.WHATSAPP)
    assert note.channel == "whatsapp"


def test_test_message_endpoint_owner_only(world):
    assert client_for(world["reception"]).post("/api/notifications/test/", {"phone": "9876543210"}, format="json").status_code == 403
    resp = client_for(world["owner"]).post("/api/notifications/test/", {"phone": "9876543210"}, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.json()["data"]["event"] == "test"


def test_resend_endpoint(world):
    m, p = mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    note = Notification.objects.get(membership=m)
    resp = client_for(world["owner"]).post(f"/api/notifications/{note.id}/resend/")
    assert resp.status_code == 200
    # With eager Celery + stub provider, resend delivers.
    note.refresh_from_db()
    assert note.status == NotificationStatus.SENT


def test_notifications_gym_isolated(world):
    mservices.enroll(gym=world["gym"], actor=world["owner"], member_id=world["member"].id, plan_id=world["plan"].id)
    other = Gym.objects.create(name="Gym B")
    ob = Branch.objects.create(gym=other, name="Main Branch")
    oo = User.objects.create_user(email="o@b.com", password="pw-123456aa", role=Role.OWNER, gym=other, branch=ob)
    assert client_for(oo).get("/api/notifications/").json()["data"]["count"] == 0
