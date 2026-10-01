"""
TenantScopedViewSet — the base every business ViewSet extends.

``get_queryset()`` ALWAYS filters by the authenticated user's gym, and further
by branch for non-owner roles. Client-supplied ``gym_id`` is ignored entirely,
so cross-tenant reads/writes are impossible even if a client tampers with input.
On create, ``gym`` (and ``branch`` where applicable) are stamped from the request.
"""
from rest_framework import viewsets

from common.permissions import IsAuthenticatedInGym
from tenants.models import Role


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedInGym]
    # Set to True on viewsets whose model has a meaningful branch scope.
    branch_scoped = True

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        qs = qs.filter(gym_id=user.gym_id)
        # Owners see the whole gym; branch-bound roles see only their branch.
        if self.branch_scoped and user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        kwargs = {"gym_id": user.gym_id}
        if self.branch_scoped and user.branch_id:
            kwargs["branch_id"] = user.branch_id
        serializer.save(**kwargs)
