from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from .models import Organizations


class AccountsPermissionHelper(PermissionHelper):
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
        if obj.id == 1:
            return False
        else:
            return True
    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class OrganizationsAdmin(ModelAdmin):
    model = Organizations
    #button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    #inspect_view_enabled = True
    menu_label = 'Organizations'  # ditch this to use verbose_name_plural from model
    menu_icon = 'group'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name',)
    search_fields = ('name',)
    permission_helper_class = AccountsPermissionHelper

    panels = [
        FieldPanel('name'),
        FieldPanel('networks'),
        FieldPanel('is_no_org'),
    ]

    '''
    def __init__(self, *args, **kwargs):
        #request = kwargs.get('request')
        #print('User ', self.current_user)
        #self.inspect_view_enabled = True
        super().__init__(*args, **kwargs)
    '''


class AccountsGroup(ModelAdminGroup):
    menu_label = 'Accounts'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (OrganizationsAdmin)


# Now you just need to register your customised ModelAdmin class with Wagtail
#modeladmin_register(AccountsGroup)
modeladmin_register(OrganizationsAdmin)
