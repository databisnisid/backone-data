from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import DpiViewSet, StarlinkViewSet

router = DefaultRouter()
router.register("dpi", DpiViewSet, basename="quota-dpi")
router.register("starlink", StarlinkViewSet, basename="quota-starlink")

urlpatterns = [path("", include(router.urls))]