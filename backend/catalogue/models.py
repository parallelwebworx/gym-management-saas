"""
Catalogue: membership Plans and Add-ons. Both are gym-wide (not branch-scoped);
prices are integer paise. Names are unique per gym, case-insensitive, among live
rows.
"""
from django.db import models
from django.db.models.functions import Lower

from common.models import TenantScoped


class PlanType(models.TextChoices):
    GENERAL = "general", "General"
    CARDIO = "cardio", "Cardio"
    GYM_CARDIO = "gym_cardio", "Gym + Cardio"
    CUSTOM = "custom", "Custom"


class AddOnType(models.TextChoices):
    ONE_TIME = "one_time", "One-time"
    RECURRING = "recurring", "Recurring"


class Plan(TenantScoped):
    name = models.CharField(max_length=120)
    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.GENERAL
    )
    duration_days = models.PositiveIntegerField()
    price_paise = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "gym",
                condition=models.Q(deleted_at__isnull=True),
                name="uniq_plan_name_per_gym_ci_alive",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class AddOn(TenantScoped):
    name = models.CharField(max_length=120)
    addon_type = models.CharField(
        max_length=20, choices=AddOnType.choices, default=AddOnType.ONE_TIME
    )
    price_paise = models.PositiveIntegerField()
    # When true, this add-on is applied automatically on a member's first
    # enrollment (e.g. a joining/admission fee). Consumed by the Phase 2
    # enrollment service.
    auto_apply_on_first_enrollment = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "gym",
                condition=models.Q(deleted_at__isnull=True),
                name="uniq_addon_name_per_gym_ci_alive",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name
