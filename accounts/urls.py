from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import OrganizationsViewSet

router = DefaultRouter()
router.register("", OrganizationsViewSet, basename="organizations")

urlpatterns = [path("", include(router.urls))]
