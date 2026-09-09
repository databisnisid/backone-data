from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Organizations


class OrganizationsSerializer(serializers.ModelSerializer):
    networks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Organizations
        fields = ("id", "name", "networks", "is_no_org")


class OrganizationsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationsSerializer
    queryset = Organizations.objects.all()