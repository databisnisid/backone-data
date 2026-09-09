from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Networks, NetworksGroup


class NetworksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Networks
        fields = ("id", "name", "network_id", "network_group")


class NetworksGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworksGroup
        fields = ("id", "name")


class NetworksViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NetworksSerializer
    queryset = Networks.objects.all()


class NetworksGroupViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NetworksGroupSerializer
    queryset = NetworksGroup.objects.all()