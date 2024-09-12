from crum import get_current_user
from django.core.exceptions import ObjectDoesNotExist
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel, ObjectList
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from django.contrib.auth.models import Group
from members.models import Members


class QuotaPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True

    '''
    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False


class QuotaDpiAdmin(ModelAdmin):
    model = Members
    menu_label = _('Siab GSM')
    menu_icon = 'tablet-alt'
    list_display_links = None
    inspect_view_enabled = False
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('service_line', 'query_current', 'quota_day', 'name')
    search_fields = ('name', 'service_line', 'quota_string' ) 
    #list_filter = ('network',)
    list_per_page = 100
    permission_helper_class = QuotaPermissionHelper

    def get_list_display(self, request):
        list_display = ('service_line', 'query_current', 'query_day', 'name')
         
        return list_display

    def get_queryset(self, request):
        #qs = Members.objects.none()
        networks = request.user.organization.networks.all()
        qs = Members.objects.filter(network__in=networks, offline_at__isnull=True, quota_string__icontains='orbit') | Members.objects.filter(network__in=networks, offline_at__gt=timezone.now(), quota_string__icontains='orbit')

        return qs


class QuotaStarlinkAdmin(ModelAdmin):
    model = Members
    menu_label = _('Starlink')
    menu_icon = 'site'
    list_display_links = None
    inspect_view_enabled = False
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('service_line', 'query_current', 'quota_day', 'name')
    search_fields = ('name', 'service_line', 'quota_string' ) 
    #list_filter = ('network',)
    list_per_page = 100
    permission_helper_class = QuotaPermissionHelper

    def get_queryset(self, request):
        #qs = Members.objects.none()
        networks = request.user.organization.networks.all()
        qs = Members.objects.filter(network__in=networks, offline_at__isnull=True, quota_string__icontains='starlink') | Members.objects.filter(network__in=networks, offline_at__gt=timezone.now(), quota_string__icontains='starlink')

        return qs


class QuotaAdminGroup(ModelAdminGroup):
    menu_label = _('Quota')
    items = (QuotaDpiAdmin, QuotaStarlinkAdmin)
    menu_icon = 'info-circle'


modeladmin_register(QuotaAdminGroup)
modeladmin_register(QuotaDpiAdmin)
