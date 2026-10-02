"""
Tenancy core: Gym (the tenant), Branch (a location within a gym), and a custom
email-login User bound to a gym/branch/role.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from tenants.managers import UserManager


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    OWNER = "owner", "Owner"
    BRANCH_MANAGER = "branch_manager", "Branch Manager"
    RECEPTIONIST = "receptionist", "Receptionist"


class SubscriptionTier(models.TextChoices):
    BASIC = "basic", "Basic"
    PRO = "pro", "Pro"


class Gym(models.Model):
    """The tenant. Every business row hangs off exactly one Gym."""

    name = models.CharField(max_length=200)
    gstin = models.CharField(max_length=15, blank=True, default="")
    invoice_prefix = models.CharField(max_length=12, default="INV")
    subscription_tier = models.CharField(
        max_length=10, choices=SubscriptionTier.choices, default=SubscriptionTier.BASIC
    )
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gym", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="uniq_branch_name_per_gym_alive",
            )
        ]

    def __str__(self):
        return f"{self.gym.name} / {self.name}"


class User(AbstractBaseUser, PermissionsMixin):
    """Email-login user scoped to a gym + (optional) branch, with a role."""

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200, blank=True, default="")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RECEPTIONIST)

    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, related_name="users", null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active", "updated_at"])
