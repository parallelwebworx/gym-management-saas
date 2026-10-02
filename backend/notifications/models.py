"""
Transactional notification records. One row per message we try to deliver to a
member on a financial event. An independent receipt to the member on every money
event is the core cash-fraud protection, so the body is server-controlled and
versioned (never free-text from a client).
"""
from django.db import models

from common.models import TenantScoped


class NotificationEvent(models.TextChoices):
    ENROLLMENT = "enrollment", "Enrollment"
    RENEWAL = "renewal", "Renewal"
    REFUND = "refund", "Refund"
    CORRECTION = "correction", "Correction"
    CANCELLATION = "cancellation", "Cancellation"
    TEST = "test", "Test"


class NotificationChannel(models.TextChoices):
    SMS = "sms", "SMS"
    WHATSAPP = "whatsapp", "WhatsApp"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Notification(TenantScoped):
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    membership = models.ForeignKey(
        "memberships.Membership", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    payment = models.ForeignKey(
        "payments.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    event = models.CharField(max_length=20, choices=NotificationEvent.choices)
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices, default=NotificationChannel.SMS)
    to_phone = models.CharField(max_length=16)
    template_version = models.CharField(max_length=12, default="v1")
    body = models.TextField()

    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    provider_message_id = models.CharField(max_length=120, blank=True, default="")
    error = models.CharField(max_length=255, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gym", "-created_at"]),
            models.Index(fields=["gym", "status"]),
        ]

    def __str__(self):
        return f"{self.event} -> {self.to_phone} [{self.status}]"
