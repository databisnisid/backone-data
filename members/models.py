from django.db import models
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalManyToManyField
from django.utils.html import format_html, format_html_join
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
    #links = models.ManyToManyField(Links, related_name='members')

    upload_baa = models.FileField(_('BAA'), upload_to='baa/', blank=True, null=True)

    notes = models.TextField(_('Notes'), blank=True)

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

    def name_with_parameters(self):
        text = format_html('{}<br /><small>{}</small>', self.name, self.get_links_html())
        #text = format_html('{}<br /><small>{}</small><br /><small>{}</small>', self.name, self.network, self.member_id)
        return text

    name_with_parameters.short_description = _('Site')
    name_with_parameters.admin_order_field = 'name'


    def get_links(self):
        return ", ".join([p.name for p in self.links.all()])
        #return self.links.all().values_list('name', flat=True)

    get_links.short_description = _('Services')

    def get_links_html(self):
        return format_html('<br />'.join([p.name for p in self.links.all()]))
    get_links_html.short_description = _('Services')


    def address_and_services(self):
        #svc_text = format_html_join('\n', '<li>{}</li>', ([p.name for p in self.links.all()]))
        #text = format_html('{}<br /><ul>{}</ul>', self.address, svc_text)
        text = format_html('{}<br /><small>{}</small>', self.address, self.get_links_html())
        return text

    address_and_services.short_description = _('Address and Services')
    address_and_services.admin_order_field = 'address'


