from django.urls import path
from rest_framework.routers import DefaultRouter

from tenants.settings_views import (
    AccountView,
    BranchViewSet,
    ChangePasswordView,
    DataExportView,
    GymSettingsView,
    SubscriptionView,
)
from tenants.views import (
    ForgotPasswordView,
    LoginView,
    MeView,
    RefreshView,
)

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("settings/gym/", GymSettingsView.as_view(), name="settings-gym"),
    path("settings/subscription/", SubscriptionView.as_view(), name="settings-subscription"),
    path("settings/account/", AccountView.as_view(), name="settings-account"),
    path("settings/password/", ChangePasswordView.as_view(), name="settings-password"),
    path("settings/export/", DataExportView.as_view(), name="settings-export"),
    *router.urls,
]
