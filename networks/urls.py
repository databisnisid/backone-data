from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import NetworksViewSet, NetworksGroupViewSet

router = DefaultRouter()
router.register("groups", NetworksGroupViewSet, basename="network-groups")

urlpatterns = [
    path("", NetworksViewSet.as_view({"get": "list"}), name="networks-list"),
    path("<int:pk>/", NetworksViewSet.as_view({"get": "retrieve", "patch": "partial_update"}), name="networks-detail"),
    path("", include(router.urls)),
]
