from django.db.models import Q

from rest_framework import serializers, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from members.models import Members
from members.rbac import sees_all_sites
from .models import Networks, NetworksGroup


class IsSuperUser(BasePermission):
    """Superuser-only write gate (V33,V34). NOT IsAdminUser — that checks is_staff,
    so a staff-but-not-superuser Wagtail admin would gain write access."""

    message = "Superuser only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class NetworksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Networks
        fields = ("id", "name", "network_id", "network_group")


def _org_scope(request):
    """Q() narrowing Members to the requester's org. Empty only for all-rows roles
    (superuser/Support); unknown or org-less users match nothing. Keeps cross-org
    site names out of the group serializer (SPEC §I)."""
    user = getattr(request, "user", None) if request is not None else None
    if user is not None and sees_all_sites(user):
        return Q()
    org = getattr(user, "organization", None) if user is not None else None
    return Q(network__in=org.networks.all()) if org else Q(pk__in=[])


class NetworksGroupSerializer(serializers.ModelSerializer):
    # V31+V34: writable direct membership list (site ids); `sites` = union of
    # network-derived (network.network_group) and directly-picked sites, deduped.
    member_sites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Members.objects.all(), required=False
    )
    sites = serializers.SerializerMethodField()
    member_sites_detail = serializers.SerializerMethodField()

    class Meta:
        model = NetworksGroup
        fields = ("id", "name", "member_sites", "member_sites_detail", "sites")

    def get_sites(self, obj):
        # Org-scoped count — same leak class as member_sites_detail.
        return (
            Members.objects.filter(Q(network__network_group=obj) | Q(network_groups=obj))
            .filter(_org_scope(self.context.get("request")))
            .distinct()
            .count()
        )

    def get_member_sites_detail(self, obj):
        # Names are the leak; member_sites (opaque ids) stays writable as-is.
        qs = obj.member_sites.filter(_org_scope(self.context.get("request")))
        return [
            {
                "id": m.pk,
                "name": m.name,
                "network_name": m.network.name if m.network else None,
            }
            for m in qs.order_by("name")
        ]


    def to_representation(self, instance):
        data = super().to_representation(instance)
        # member_sites is writable, so scope the OUTPUT only (ids still enumerate
        # cross-org sites otherwise).
        scope = _org_scope(self.context.get("request"))
        if scope:
            keep = set(
                instance.member_sites.filter(scope).values_list("id", flat=True)
            )
            data["member_sites"] = [i for i in data["member_sites"] if i in keep]
        return data

class NetworksViewSet(viewsets.mixins.RetrieveModelMixin, viewsets.mixins.ListModelMixin, viewsets.mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Read list/detail for any authed user; PATCH (assign network_group) is
    superuser-only (V33) via get_permissions."""

    permission_classes = [IsAuthenticated]
    serializer_class = NetworksSerializer

    def get_queryset(self):
        # Org-scoped list/detail (SPEC §I): any authed user may GET, but only
        # their own org's networks. Ordered — paginated list needs a stable sort.
        if sees_all_sites(self.request.user):
            return Networks.objects.order_by("id")
        org = getattr(self.request.user, "organization", None)
        return org.networks.order_by("id") if org else Networks.objects.none()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [permission() for permission in self.permission_classes]
        return [permission() for permission in [IsSuperUser]]


class NetworksGroupViewSet(viewsets.ModelViewSet):
    """Writable group CRUD (T1/T2 + V34). Create/rename/delete groups, assign networks
    by setting each network's network_group FK, and pick member sites directly via the
    member_sites M2M. Delete SET_NULL-orphans networks (V32); never deletes sites."""

    permission_classes = [IsAuthenticated]
    serializer_class = NetworksGroupSerializer
    queryset = NetworksGroup.objects.all()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [permission() for permission in self.permission_classes]
        return [permission() for permission in [IsSuperUser]]

    def perform_destroy(self, instance):
        # V32: on_delete=SET_NULL (model) already orphans the group's networks; nothing
        # extra to cascade because site membership is derived via network, never FK'd.
        instance.delete()
