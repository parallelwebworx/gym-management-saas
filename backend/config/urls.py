"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"ok": True, "data": {"status": "healthy"}})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/", include("tenants.urls")),
    path("api/", include("catalogue.urls")),
    path("api/", include("members.urls")),
    path("api/", include("memberships.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("engagement.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("reports.urls")),
]
