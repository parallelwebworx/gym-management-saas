"""
Append-only audit log. Every financial/membership mutation records a row via
``audit.record()``. The Phase 4 viewer reads these; here we only write them.

Append-only is enforced at the app layer: the model's ``save`` refuses updates
and ``delete`` is blocked. (A DB trigger could harden this further later.)
"""
from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    ENROLL = "enroll", "Enroll"
    RENEW = "renew", "Renew"
    REFUND = "refund", "Refund"
    EDIT_PAYMENT = "edit_payment", "Edit payment"
    CORRECT = "correct", "Correct membership"
    CANCEL = "cancel", "Cancel membership"


class AuditLog(models.Model):
    gym = models.ForeignKey("tenants.Gym", on_delete=models.CASCADE, related_name="audit_logs")
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    entity_type = models.CharField(max_length=60)
    entity_id = models.CharField(max_length=40)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    summary = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gym", "-created_at"]),
            models.Index(fields=["gym", "entity_type", "entity_id"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditLog is append-only; rows cannot be updated.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog is append-only; rows cannot be deleted.")

    def __str__(self):
        return f"{self.action} {self.entity_type}#{self.entity_id} by {self.actor_id}"
