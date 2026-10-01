"""
TenantMiddleware — resolves the tenant context from the authenticated user and
attaches it to the request as ``request.gym`` / ``request.branch`` / ``request.role``.

DRF authenticates *inside* the view (after middleware runs), so ``request.user``
is still lazy here. We therefore attach lightweight callables that resolve on
first access, once auth has populated ``request.user``. ViewSets read these in
``get_queryset()`` — see ``common.viewsets``.

The tenant is ALWAYS derived from the server-side user record; a client-supplied
``gym_id`` is never trusted.
"""


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def _gym():
            user = getattr(request, "user", None)
            return getattr(user, "gym", None) if user and user.is_authenticated else None

        def _branch():
            user = getattr(request, "user", None)
            return getattr(user, "branch", None) if user and user.is_authenticated else None

        def _role():
            user = getattr(request, "user", None)
            return getattr(user, "role", None) if user and user.is_authenticated else None

        # SimpleLazyObject-style: expose as properties via a small helper.
        request.get_gym = _gym
        request.get_branch = _branch
        request.get_role = _role
        return self.get_response(request)
