"""
Role-based DRF permission classes.

Roles (see ``tenants.models.Role``):
  - super_admin  : platform operator (CLI-provisioned)
  - owner        : full access across all branches of a gym
  - branch_manager: single-branch management, no owner-only financial reports
  - receptionist : front-desk; no reports/audit, no deletes/refunds

Phase 0 ships the building blocks; per-action wiring lands with each feature.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

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


class ReadAnyWriteRoles(BasePermission):
    """
    Safe methods: any authenticated in-gym user. Unsafe methods: only
    ``write_roles``. Subclass via ``ReadAnyWriteRoles.for_roles(...)``.

    Used for the catalogue (receptionist is read-only) and anywhere reads are
    open to all staff but mutations are restricted.
    """

    write_roles: tuple[str, ...] = (Role.OWNER, Role.BRANCH_MANAGER)

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.gym_id):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in self.write_roles

    @classmethod
    def for_roles(cls, *roles):
        return type(
            f"ReadAnyWriteRoles_{'_'.join(roles)}",
            (cls,),
            {"write_roles": tuple(roles)},
        )


class MemberPermission(BasePermission):
    """
    Members: any in-gym staff may read/create/update; only owner/manager may
    delete (receptionists cannot delete — matches the source RBAC).
    """

    delete_roles = (Role.OWNER, Role.BRANCH_MANAGER)

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.gym_id):
            return False
        if request.method == "DELETE":
            return user.role in self.delete_roles
        return True
