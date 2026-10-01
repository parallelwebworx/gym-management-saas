"""Auth + tenant context endpoints."""
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.responses import err, ok
from tenants.models import Branch, User
from tenants.serializers import BranchSerializer, MeSerializer


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class LoginView(APIView):
    """POST {email, password} -> {access, refresh, user} in the envelope."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        if not email or not password:
            return err("Email and password are required.", code="missing_credentials")

        user = User.objects.filter(email=email, deleted_at__isnull=True).first()
        if not user or not user.is_active or not user.check_password(password):
            return err("Invalid credentials.", code="invalid_credentials", status=401)

        data = _issue_tokens(user)
        data["user"] = MeSerializer(user).data
        return ok(data)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return err("Refresh token required.", code="missing_token")
        try:
            refresh = RefreshToken(token)
            return ok({"access": str(refresh.access_token)})
        except TokenError:
            return err("Invalid or expired refresh token.", code="invalid_token", status=401)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ok(MeSerializer(request.user).data)


class ForgotPasswordView(APIView):
    """Scaffold — always returns ok to avoid account enumeration.

    Real email dispatch (token generation + send) lands with the notifications
    integration in Phase 5.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        # Intentionally does not reveal whether the email exists.
        return ok({"message": "If the account exists, a reset link has been sent."})


class BranchListView(APIView):
    """Branches visible to the current user's gym."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Branch.objects.filter(gym_id=request.user.gym_id, deleted_at__isnull=True)
        return ok(BranchSerializer(qs, many=True).data)
