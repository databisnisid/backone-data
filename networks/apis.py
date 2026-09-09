from django.db.models import Q

from rest_framework import serializers, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from members.models import Members
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
        return (
            Members.objects.filter(Q(network__network_group=obj) | Q(network_groups=obj))
            .distinct()
            .count()
        )

    def get_member_sites_detail(self, obj):
        return [
            {
                "id": m.pk,
                "name": m.name,
                "network_name": m.network.name if m.network else None,
            }
            for m in obj.member_sites.all().order_by("name")
        ]




class NetworksViewSet(viewsets.mixins.RetrieveModelMixin, viewsets.mixins.ListModelMixin, viewsets.mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Read list/detail for any authed user; PATCH (assign network_group) is
    superuser-only (V33) via get_permissions."""

    permission_classes = [IsAuthenticated]
    serializer_class = NetworksSerializer
    queryset = Networks.objects.all()

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
