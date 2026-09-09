from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_members_by_user
from .apis import SitesViewSet, MemberLinkViewSet

router = DefaultRouter()
router.register("sites", SitesViewSet, basename="sites")
router.register("links", MemberLinkViewSet, basename="links")

urlpatterns = [
    path("get_by_user/<int:user>/", get_members_by_user, name="get-members-by-user"),
    path("", include(router.urls)),
]
