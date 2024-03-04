from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Networks, NetworksGroup


class NetworksPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True

    '''
    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class NetworksAdmin(ModelAdmin):
    model = Networks
    menu_labels = _('Networks')
    menu_icon = 'link'
    #inspect_view_enabled = True
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'network_id', 'network_group')
    search_fields = ('name', ) 
    list_filter = ('network_group',)
    list_per_page = 100
    permission_helper_class = NetworksPermissionHelper

    panels = [
            MultiFieldPanel([
                FieldPanel('name', read_only=True),
                FieldPanel('network_id', read_only=True),
                ], heading=_('Site and Network')),
            FieldPanel('network_group'),
            ]

class NetworksGroupAdmin(ModelAdmin):
    model = NetworksGroup
    menu_labels = _('Networks Group')
    menu_icon = 'grip'
    #inspect_view_enabled = True
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name',)
    search_fields = ('name', ) 
    list_per_page = 100
    #permission_helper_class = NetworksPermissionHelper

    panels = [
            FieldPanel('name'),
            ]

class NetworksAdminGroup(ModelAdminGroup):
    menu_label = _('Networks')
    menu_order = 10000
    menu_icon = 'link'
    items = (NetworksAdmin, NetworksGroupAdmin)


modeladmin_register(NetworksAdminGroup)
#modeladmin_register(NetworksGroupAdmin)

