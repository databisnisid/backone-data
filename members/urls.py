from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_members_by_user
from .apis import (
    SitesViewSet,
    MemberLinkViewSet,
    SdwanLookupViewSet,
    BaaLookupViewSet,
    RoleLookupViewSet,
    ProviderLookupViewSet,
)


router = DefaultRouter()
router.register("sites", SitesViewSet, basename="sites")
router.register("links", MemberLinkViewSet, basename="links")
# Fixed per-kind paths (review NOTE: DefaultRouter can't param `{kind}`).
router.register("lookups/sdwan", SdwanLookupViewSet, basename="lookups-sdwan")
router.register("lookups/baa", BaaLookupViewSet, basename="lookups-baa")
router.register("lookups/role", RoleLookupViewSet, basename="lookups-role")
router.register("lookups/provider", ProviderLookupViewSet, basename="lookups-provider")


urlpatterns = [
    path("get_by_user/<int:user>/", get_members_by_user, name="get-members-by-user"),
    path("options/", SitesViewSet.as_view({"get": "options"}), name="members-options"),
    path("", include(router.urls)),
]
