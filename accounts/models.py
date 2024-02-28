from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from networks.models import Networks


class Organizations(models.Model):
    name = models.CharField(_('Name'), max_length=50, unique=True)

    networks = models.ManyToManyField(Networks)

    is_no_org = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'organizations'
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')

    def __str__(self):
        return '%s' % self.name


class User(AbstractUser):
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        blank=True,
        null=True,
    )


