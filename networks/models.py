from django.db import models
from django.utils.translation import gettext_lazy as _


class NetworksGroup(models.Model):
    name = models.CharField(_('Network Group'), max_length=50)

    # V34: optional direct site membership (union with network-derived sites).
    # String ref avoids circular import (members.models imports networks.models).
    member_sites = models.ManyToManyField(
        'members.Members',
        verbose_name=_('Member Sites'),
        blank=True,
        related_name='network_groups',
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'networks_group'
        verbose_name = _('Network Group')
        verbose_name_plural = _('Networks Group')

    def __str__(self):
        return '%s' % self.name


class Networks(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    description = models.TextField(_('Description'), blank=True)
    network_id = models.CharField(_('Network ID'), max_length=50, unique=True)

    # Upstream instance owning this row: netloc of sync_data()'s domain_api.
    # Scopes sync deletion so one domain's absence from its own API can never
    # delete another domain's rows. ponytail: plain CharField, no FK/choices —
    # upgrade to a Domain table if a third instance ever appears.
    domain = models.CharField(_('Source Domain'), max_length=100, blank=True, default='')

    network_group = models.ForeignKey(
            NetworksGroup,
            on_delete=models.SET_NULL,
            verbose_name=_('Network Group'),
            blank=True,
            null=True
            )

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


