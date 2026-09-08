from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from django.utils.translation import gettext_lazy as _
from .models import Links


class LinksViewSet(SnippetViewSet):
    model = Links
    menu_label = 'Services'
    menu_icon = 'link-external'
    add_to_admin_menu = True
    menu_order = 300
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 100
    panels = [
        FieldPanel('name'),
    ]

    def user_can_delete_obj(self, request, obj):
        return False


register_snippet(LinksViewSet)
