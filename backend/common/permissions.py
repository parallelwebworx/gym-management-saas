"""
Role-based DRF permission classes.

Roles (see ``tenants.models.Role``):
  - super_admin  : platform operator (CLI-provisioned)
  - owner        : full access across all branches of a gym
  - branch_manager: single-branch management, no owner-only financial reports
  - receptionist : front-desk; no reports/audit, no deletes/refunds

Phase 0 ships the building blocks; per-action wiring lands with each feature.
"""
from rest_framework.permissions import BasePermission

from tenants.models import Role


class IsAuthenticatedInGym(BasePermission):
    """Authenticated AND attached to a gym (rejects orphaned/super-admin-less users)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.gym_id)


class RoleAllowed(BasePermission):
    """
    Base class: subclass and set ``allowed_roles``. Use directly via
    ``RoleAllowed.for_roles(Role.OWNER, Role.BRANCH_MANAGER)`` in a view.
    """

    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.gym_id):
            return False
        return user.role in self.allowed_roles

    @classmethod
    def for_roles(cls, *roles):
        return type(
            f"RoleAllowed_{'_'.join(roles)}",
            (cls,),
            {"allowed_roles": tuple(roles)},
        )


IsOwner = RoleAllowed.for_roles(Role.OWNER)
IsOwnerOrManager = RoleAllowed.for_roles(Role.OWNER, Role.BRANCH_MANAGER)
