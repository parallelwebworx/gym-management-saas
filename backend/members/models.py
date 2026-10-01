"""
Member — a gym customer, scoped to a gym + branch. Phone is stored E.164 and is
unique per gym among live (non-soft-deleted) rows. Fuzzy name/phone search uses
pg_trgm on Postgres (see migration 0002); other backends fall back to icontains.
"""
from django.db import models

from common.models import TenantScoped


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    UNSPECIFIED = "unspecified", "Unspecified"


class Member(TenantScoped):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=16)  # E.164, e.g. +919876543210
    email = models.EmailField(blank=True, default="")
    gender = models.CharField(
        max_length=12, choices=Gender.choices, default=Gender.UNSPECIFIED
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gym", "phone"],
                condition=models.Q(deleted_at__isnull=True),
                name="uniq_member_phone_per_gym_alive",
            )
        ]
        indexes = [
            models.Index(fields=["gym", "full_name"]),
            models.Index(fields=["gym", "created_at"]),
        ]
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.phone})"
