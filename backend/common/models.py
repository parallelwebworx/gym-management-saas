"""
Cross-cutting base model + managers for multi-tenant, soft-deleted rows.

Every business table in this app subclasses ``TenantScoped``: it carries a
``gym`` FK (hard tenant boundary), an optional ``branch`` FK, and the standard
``created_at / updated_at / deleted_at`` timestamps. Soft-delete is the default —
``objects`` hides deleted rows; ``all_objects`` sees everything.

Tenant *isolation* is enforced at the API layer (see ``common.viewsets`` and
``common.middleware``); this module only provides the shared shape + soft-delete
semantics. Do not rely on a model manager alone for isolation — always filter by
``request.gym`` in ``get_queryset()``.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """Soft-delete the whole queryset (no rows are physically removed)."""
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)


class TenantManager(models.Manager):
    """Default manager: only rows that have not been soft-deleted."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )


class AllObjectsManager(models.Manager):
    """Escape hatch: every row, including soft-deleted ones."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft-delete a single instance."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])


class TenantScoped(TimeStampedModel):
    """
    Base for every gym-owned table. ``gym`` is the hard tenant boundary;
    ``branch`` is an optional finer scope (null = gym-wide).
    """

    gym = models.ForeignKey(
        "tenants.Gym",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    branch = models.ForeignKey(
        "tenants.Branch",
        on_delete=models.PROTECT,
        related_name="%(class)ss",
        null=True,
        blank=True,
    )

    objects = TenantManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        base_manager_name = "objects"
