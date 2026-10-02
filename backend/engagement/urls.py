from django.urls import path
from rest_framework.routers import DefaultRouter

from engagement.views import ReminderViewSet, TodayView

router = DefaultRouter()
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path("today/", TodayView.as_view(), name="today"),
    *router.urls,
]
