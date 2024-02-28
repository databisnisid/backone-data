from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from .models import Members


class MembersPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False
    '''

    def user_can_delete_obj(self, user, obj):
            return False

    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class MembersAdmin(ModelAdmin):
    model = Members
    menu_labels = _('Members')
    menu_icon = 'globe'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name_with_network', 'address', 'online_at')
    search_fields = ('name', 'network__name', 'member_id')
    #list_filter = ('network',)
    list_per_page = 100
    permission_helper_class = MembersPermissionHelper

    panels = [
            MultiFieldPanel([
                FieldPanel('name', read_only=True),
                #FieldPanel('description', read_only=True),
                FieldPanel('network', read_only=True),
                ], heading=_('Site and Network')),
            FieldPanel('address', read_only=True),
            #GeoAddressPanel("address", geocoder=geocoders.GOOGLE_MAPS, read_only=True),
            #GoogleMapsPanel('location', address_field='address', read_only=True),
            FieldRowPanel([
                FieldPanel('online_at', read_only=True),
                FieldPanel('offline_at', read_only=True),
                ])
            ]

    def get_list_display(self, request):
        if request.user.is_superuser:
            list_display = ('name_with_network', 'address', 'online_at', 'offline_at')
        else:
            list_display = ('name_with_network', 'address', 'online_at')
         
        return list_display

    def get_queryset(self, request):
        #qs = Members.objects.none()
        if request.user.is_superuser:
            qs = Members.objects.all()
        else:
            networks = request.user.organization.networks.all()
            qs = Members.objects.filter(network__in=networks, offline_at__isnull=True) | Members.objects.filter(network__in=networks, offline_at__gt=timezone.now())
            #qs = Members.objects.filter(network__in=networks)
            '''
            for network in request.user.organization.networks.all():
                print(network)
                qs_net = Members.objects.filter(network=network)
                qs = qs | qs_net
            '''

        return qs

modeladmin_register(MembersAdmin)

