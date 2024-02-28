from wagtail.admin.ui.components import Component
from django.conf import settings
from crum import get_current_user
from django.utils.translation import gettext as _


class MapSummaryPanel(Component):
    order = 10
    template_name = "dashboard/map_dashboard.html"

    def __init__(self):
        user = get_current_user()
        self.user = user

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['settings'] = settings
        context['user'] = self.user

        return context


