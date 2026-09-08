from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from .models import Organizations


class OrganizationsViewSet(SnippetViewSet):
    model = Organizations
    menu_label = 'Organizations'
    menu_icon = 'group'
    menu_order = 200
    add_to_settings_menu = True
    list_display = ('name',)
    search_fields = ('name',)
    panels = [
        FieldPanel('name'),
        FieldPanel('networks'),
        FieldPanel('is_no_org'),
    ]

    def user_can_create(self, request):
        return request.user.is_superuser

    def user_can_delete_obj(self, request, obj):
        if obj.id == 1:
            return False
        return True


register_snippet(OrganizationsViewSet)
