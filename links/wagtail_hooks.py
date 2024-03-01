from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from .models import Links


class LinksPermissionHelper(PermissionHelper):
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


class LinksAdmin(ModelAdmin):
    model = Links
    menu_labels = _('Services')
    menu_icon = 'link-external'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name',)
    search_fields = ('name',)
    #list_filter = ('network',)
    list_per_page = 100
    permission_helper_class = LinksPermissionHelper

    panels = [
            FieldPanel('name'),
            ]

modeladmin_register(LinksAdmin)

