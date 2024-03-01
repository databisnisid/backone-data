from django.db import models
from django.utils.translation import gettext_lazy as _


class Networks(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    description = models.TextField(_('Description'), blank=True)
    network_id = models.CharField(_('Network ID'), max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    '''
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Owner'),
        null=True
    )

    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )
    '''

    class Meta:
        db_table = 'networks'
        verbose_name = _('Network')
        verbose_name_plural = _('Networks')

    def __str__(self):
        return '%s' % self.name


'''
class NetworksGroup(models.Model):
    name = models.CharField(_('Network Group'), max_lenth=50)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'networks_group'
        verbose_name = _('Network Group')
        verbose_name_plural = _('Networks Group')

    def __str__(self):
        return '%s' % self.name
'''
