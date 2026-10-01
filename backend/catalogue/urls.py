from rest_framework.routers import DefaultRouter

from catalogue.views import AddOnViewSet, PlanViewSet

router = DefaultRouter()
router.register("plans", PlanViewSet, basename="plan")
router.register("add-ons", AddOnViewSet, basename="addon")

urlpatterns = router.urls
