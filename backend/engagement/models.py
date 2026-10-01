"""
Lightweight reminder tracking for the Today's View. A Reminder records that a
staff member reached out to a member (WhatsApp / call / SMS) about an expiry or
renewal — so the front desk can see who has already been contacted.
"""
from django.conf import settings
from django.db import models

from common.models import TenantScoped


class ReminderChannel(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    CALL = "call", "Call"
    SMS = "sms", "SMS"
    OTHER = "other", "Other"


class Reminder(TenantScoped):
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="reminders")
    membership = models.ForeignKey(
        "memberships.Membership", on_delete=models.SET_NULL, null=True, blank=True, related_name="reminders"
    )
    channel = models.CharField(max_length=12, choices=ReminderChannel.choices, default=ReminderChannel.WHATSAPP)
    note = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reminders_created"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["gym", "member", "-created_at"])]

    def __str__(self):
        return f"{self.channel} to member={self.member_id}"
