from django.urls import path

from tenants.views import (
    BranchListView,
    ForgotPasswordView,
    LoginView,
    MeView,
    RefreshView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("branches/", BranchListView.as_view(), name="branch-list"),
]
