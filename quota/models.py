from weakref import proxy
from django.db import models
from members.models import Members


class DpiManager(models.Manager):
    def get_queryset(self):
        return super(DpiManager, self).get_queryset().filter(quota_string__contains='dpi')


class StarlinkManager(models.Manager):
    def get_queryset(self):
        return super(StarlinkManager, self).get_queryset().filter(quota_string__contains='starlink')


class MembersDpi(Members):
    objects = DpiManager()

    class Meta:
        proxy = True

class MembersStarlink(Members):
    objects = StarlinkManager()

    class Meta:
        proxy = True

