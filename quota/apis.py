from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from members.serializers import MemberSerializer
from members.apis import member_queryset_for
from .models import MembersDpi, MembersStarlink


class QuotaBaseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MemberSerializer

    def get_queryset(self):
        base = self.model.objects.all()
        allowed_ids = member_queryset_for(self.request.user).values_list("id", flat=True)
        return base.filter(id__in=allowed_ids)


class DpiViewSet(QuotaBaseViewSet):
    model = MembersDpi


class StarlinkViewSet(QuotaBaseViewSet):
    model = MembersStarlink