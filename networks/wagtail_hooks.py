from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, InlinePanel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Networks, NetworksGroup


class NetworksViewSet(SnippetViewSet):
    model = Networks
    menu_label = 'Networks'
    menu_icon = 'link'
    add_to_admin_menu = True
    add_to_settings_menu = False
    menu_order = 200
    exclude_from_explorer = False
    list_display = ('name', 'network_id', 'network_group')
    search_fields = ('name', 'network_id',)
    list_filter = ('network_group',)
    list_per_page = 100
    panels = [
        MultiFieldPanel([
            FieldPanel('name', read_only=True),
            FieldPanel('network_id', read_only=True),
        ], heading='Site and Network'),
        FieldPanel('network_group'),
    ]

    def user_can_create(self, request):
        return False

    def user_can_delete_obj(self, request, obj):
        return False


class NetworksGroupViewSet(SnippetViewSet):
    model = NetworksGroup
    menu_label = 'Networks Group'
    menu_icon = 'grip'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 100
    panels = [
        FieldPanel('name'),
    ]


register_snippet(NetworksViewSet)
register_snippet(NetworksGroupViewSet)
