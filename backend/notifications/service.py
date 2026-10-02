"""
Notification orchestration: build the server-controlled body, persist a pending
row inside the caller's transaction, and schedule async delivery post-commit.
"""
from django.db import transaction
from django.utils import timezone

from notifications import templates_registry as templates
from notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from notifications.providers import ProviderError, get_provider


def _channel_for(gym, requested):
    # WhatsApp is a Pro-tier feature; everyone else falls back to SMS.
    if requested == NotificationChannel.WHATSAPP and gym.subscription_tier == "pro":
        return NotificationChannel.WHATSAPP
    return NotificationChannel.SMS


def queue_notification(*, gym, event, member=None, membership=None, payment=None,
                       channel=NotificationChannel.SMS, extra=None):
    """Create a PENDING notification (within the current transaction) and schedule
    delivery once that transaction commits. Returns the Notification, or None if
    there's no phone to send to."""
    if member is None and membership is not None:
        member = membership.member
    if member is None or not member.phone:
        return None

    ctx = {
        "member_name": member.full_name,
        "gym_name": gym.name,
        "plan_name": membership.plan_name if membership else "",
        "end_date": membership.end_date.isoformat() if membership else "",
        "amount_paise": payment.amount_paise if payment else 0,
        "invoice_number": payment.invoice_number if payment else "",
        "effective_date": (membership.cancel_effective_date.isoformat()
                           if membership and membership.cancel_effective_date else ""),
    }
    if extra:
        ctx.update(extra)

    body = templates.render(event, ctx)
    chan = _channel_for(gym, channel)

    note = Notification.objects.create(
        gym=gym, branch=(membership.branch if membership else member.branch),
        member=member, membership=membership, payment=payment,
        event=event, channel=chan, to_phone=member.phone,
        template_version=templates.TEMPLATE_VERSION, body=body,
    )
    # Deliver after the surrounding financial transaction commits.
    from notifications.tasks import send_notification_task
    transaction.on_commit(lambda: send_notification_task.delay(note.id))
    return note


def attempt_send(notification: Notification) -> bool:
    """Try to deliver one notification. Updates status/attempts. Returns success.

    Raises ProviderError on failure so the Celery task can retry.
    """
    notification.attempts += 1
    try:
        provider = get_provider()
        msg_id = provider.send(notification.to_phone, notification.body, notification.channel)
    except ProviderError as exc:
        notification.status = NotificationStatus.FAILED
        notification.error = str(exc)[:255]
        notification.save(update_fields=["attempts", "status", "error", "updated_at"])
        raise
    notification.status = NotificationStatus.SENT
    notification.provider_message_id = msg_id
    notification.error = ""
    notification.sent_at = timezone.now()
    notification.save(update_fields=[
        "attempts", "status", "provider_message_id", "error", "sent_at", "updated_at",
    ])
    return True
