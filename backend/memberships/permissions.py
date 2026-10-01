"""
Membership-correction permission matrix (ported from the source app). A single
predicate used by BOTH the API and the UI so the rule never drifts between them.

  - receptionist  : within 60 minutes of enrollment AND the same enroller
  - branch_manager: same IST day as enrollment AND the same branch
  - owner         : within 90 days of enrollment
  - super_admin   : always
"""
from datetime import timedelta

from common.dates import IST, ist_now
from tenants.models import Role


def can_correct_membership(user, membership) -> tuple[bool, str]:
    """Return (allowed, reason-if-not)."""
    created = membership.created_at
    now = ist_now()

    if user.role == Role.SUPER_ADMIN:
        return True, ""

    if user.role == Role.OWNER:
        if now - created <= timedelta(days=90):
            return True, ""
        return False, "Owners can correct within 90 days of enrollment."

    if user.role == Role.BRANCH_MANAGER:
        same_branch = membership.branch_id == user.branch_id
        same_day = created.astimezone(IST).date() == now.astimezone(IST).date()
        if same_branch and same_day:
            return True, ""
        if not same_branch:
            return False, "Managers can only correct memberships in their own branch."
        return False, "Managers can correct only on the same day as enrollment."

    if user.role == Role.RECEPTIONIST:
        if membership.created_by_id != user.id:
            return False, "Receptionists can correct only their own enrollments."
        if now - created <= timedelta(minutes=60):
            return True, ""
        return False, "Receptionists can correct within 60 minutes of enrollment."

    return False, "Not permitted."
