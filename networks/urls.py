from django.urls import path
from rest_framework.generics import ListAPIView
from .apis import NetworksViewSet, NetworksGroupViewSet

list_nets = ListAPIView.as_view(
    queryset=NetworksViewSet.queryset, serializer_class=NetworksViewSet.serializer_class,
    permission_classes=NetworksViewSet.permission_classes,
)
list_groups = ListAPIView.as_view(
    queryset=NetworksGroupViewSet.queryset, serializer_class=NetworksGroupViewSet.serializer_class,
    permission_classes=NetworksGroupViewSet.permission_classes,
)

urlpatterns = [
    path("", list_nets, name="networks-list"),
    path("groups/", list_groups, name="network-groups-list"),
]