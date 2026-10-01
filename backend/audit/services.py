"""Helper to write audit rows from service-layer code."""
from audit.models import AuditLog


def record(*, actor, action, entity, before=None, after=None, summary="", gym=None, branch=None):
    """Append an audit row. ``entity`` is any model instance (used for type/id)."""
    entity_type = entity.__class__.__name__
    gym_id = gym.id if gym is not None else getattr(entity, "gym_id", None)
    branch = branch if branch is not None else getattr(entity, "branch", None)
    return AuditLog.objects.create(
        gym_id=gym_id,
        branch=branch,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity.pk),
        before=before,
        after=after,
        summary=summary,
    )
