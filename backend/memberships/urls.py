from rest_framework.routers import DefaultRouter

from memberships.views import MembershipViewSet

router = DefaultRouter()
router.register("memberships", MembershipViewSet, basename="membership")

urlpatterns = router.urls
