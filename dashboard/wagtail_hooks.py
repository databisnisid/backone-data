#from django.http import HttpRequest
#from django.utils.safestring import mark_safe
#from wagtail.admin.ui.components import Component
from django.core.exceptions import ObjectDoesNotExist
from wagtail import hooks

from dashboard.summary_panels import NetworksPanelSummary
#from networks.models import Networks, NetworkRoutes
#from members.models import Members
#from crum import get_current_user
#from wagtail.contrib.modeladmin.views import CreateView, EditView
from .summary_panels import *
#from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.contrib.auth.models import Group
#from axes.models import AccessAttempt, AccessLog, AccessFailureLog
#from wagtail.snippets.models import register_snippet
#from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
#from django.conf import settings


@hooks.register('construct_reports_menu', order=1)
def hide_reports_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'workflows']
    menu_items[:] = [item for item in menu_items if item.name != 'workflow-tasks']
    menu_items[:] = [item for item in menu_items if item.name != 'aging-pages']
    menu_items[:] = [item for item in menu_items if item.name != 'locked-pages']


@hooks.register('construct_main_menu', order=2)
def hide_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'documents']
    menu_items[:] = [item for item in menu_items if item.name != 'explorer']
    menu_items[:] = [item for item in menu_items if item.name != 'images']
    menu_items[:] = [item for item in menu_items if item.name != 'help']

    try:
        group_support = Group.objects.get(name='Support')
    except ObjectDoesNotExist:
        group_support = []

    #if not request.user.is_superuser or request.user.group not in group_support:
    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != 'networks']

    if not group_support in request.user.groups.all():
        menu_items[:] = [item for item in menu_items if item.name != 'networks']

    '''
    if not request.user.is_superuser:
        if not request.user.organization.features.network_rules:
            menu_items[:] = [item for item in menu_items if item.name != 'network-rules']

    if not request.user.is_superuser:
        if not request.user.organization.features.is_webfilter:
            menu_items[:] = [item for item in menu_items if item.name != 'waf']
            #menu_items[:] = [item for item in menu_items if item.name != 'webfilters']

    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != 'memberpeers']
        menu_items[:] = [item for item in menu_items if item.name != 'controllers']
        menu_items[:] = [item for item in menu_items if item.name != 'backone-hs']

    if settings.HEADSCALE_ON == 0:
        menu_items[:] = [item for item in menu_items if item.name != 'backone-hs']
    '''


@hooks.register("construct_settings_menu", order=3)
def hide_user_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "workflows"]
    menu_items[:] = [item for item in menu_items if item.name != "workflow-tasks"]
    menu_items[:] = [item for item in menu_items if item.name != "redirects"]
    menu_items[:] = [item for item in menu_items if item.name != "sites"]
    menu_items[:] = [item for item in menu_items if item.name != "collections"]

@hooks.register('construct_homepage_panels', order=4)
def add_another_welcome_panel(request, panels):
    panels[:] = [panel for panel in panels if panel.name != "site_summary"]
    panels[:] = [panel for panel in panels if panel.name != "workflow_pages_to_moderate"]
    panels[:] = [panel for panel in panels if panel.name != "pages_for_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "user_pages_in_workflow_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "locked_pages"]

    panels.append(MapSummaryPanel())
    panels.append(NetworksPanelSummary())

'''

    #panels.append(NetworksSummaryPanel())
    #panels.append(MembersProblemPanel())
    panels.append(MemberChartsPanel())
    panels.append(ModelChartsPanel())
    if request.user.is_superuser:
        panels.append(NetworksChartsPanel())
    if request.user.organization.features.number_of_network > 1:
        panels.append(NetworksChartsPanel())

'''

'''
@hooks.register("insert_global_admin_js", order=100)
def global_admin_js():
    """Add /static/css/custom.js to the admin."""
    return format_html(
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
    )
'''

'''
class AccessAttemptSVS(SnippetViewSet):
    model = AccessAttempt
    menu_label = _('Access Attempt')
    icon = 'lock-open'
    inspect_view_enabled = True
    #index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
            "attempt_time",
            "ip_address",
            "user_agent",
            "username",
            "path_info",
            "failures_since_start"
            ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
            "user_agent",
            "ip_address",
            "username",
            "http_accept",
            "path_info",
            "attempt_time",
            "get_data",
            "post_data",
            "failures_since_start",
            ]

class AccessLogSVS(SnippetViewSet):
    model = AccessLog
    menu_label = _('Access Log')
    icon = 'list-ul'
    #index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
            "attempt_time",
            "logout_time",
            "ip_address",
            "username",
            "user_agent",
            "path_info",
            ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
            "user_agent",
            "ip_address",
            "username",
            "http_accept",
            "path_info",
            "attempt_time",
            "logout_time",
            ]

class AccessFailureLogSVS(SnippetViewSet):
    model = AccessFailureLog
    menu_label = _('Access Failure')
    icon = 'chain-broken'
    #index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
            "attempt_time",
            "ip_address",
            "username",
            "user_agent",
            "path_info",
            "locked_out",
            ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
            "user_agent",
            "ip_address",
            "username",
            "http_accept",
            "path_info",
            "attempt_time",
            "locked_out",
            ]


class AccessSnippetGroup(SnippetViewSetGroup):
    items = (AccessAttemptSVS, AccessFailureLogSVS, AccessLogSVS)
    menu_label = _('Access')
    menu_icon = 'lock'

register_snippet(AccessSnippetGroup)

'''
