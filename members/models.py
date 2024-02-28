from django.db import models
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalManyToManyField
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from networks.models import Networks
from links.models import Links


#class Members(models.Model):
class Members(ClusterableModel):
    name = models.CharField(_('Member Name'), max_length=50)
    member_code = models.CharField(_('Member Code'), max_length=20, blank=True, null=True)
    description = models.TextField(_('Description'), blank=True)
    member_id = models.CharField(_('Member ID'), max_length=50, unique=True)

    address = models.CharField(_('Address'), max_length=250, blank=True, null=True)
    location = models.CharField(_('Location'), max_length=250, blank=True, null=True)

    online_at = models.DateField(_('Start Online'), blank=True, null=True)
    offline_at = models.DateTimeField(_('Stop Online'), blank=True, null=True)

    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        #limit_choices_to=limit_choices_to_current_user,
        verbose_name=_('Network'),
    )

    links = ParentalManyToManyField(Links, related_name='members')

    upload_baa = models.FileField(_('BAA'), upload_to='baa/', blank=True, null=True)


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

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    
    class Meta:
        db_table = 'members'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'


    def __str__(self):
        return '%s' % self.name

    def delete(self, *args, **kwargs):
        if self.upload_baa:
            self.upload_baa.delete()
        super().delete(*args, **kwargs)

    def name_with_network(self):
        text = format_html('{}<br /><small>{}</small>', self.name, self.network)
        return text

    name_with_network.short_description = _('Site Name')
    name_with_network.admin_order_field = 'name'


    def get_links(self):
        return list(self.links.all())

    get_links.short_description = _('Services')
    get_links.admin_order_field = 'links'


