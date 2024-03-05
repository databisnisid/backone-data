from wagtail.admin.ui.components import Component
from django.conf import settings
from crum import get_current_user
from django.utils.translation import gettext as _
from django.db.models import Count
from networks.models import Networks, NetworksGroup
from accounts.models import User
from members.models import Members


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


class NetworksPanelSummary(Component):
    order = 20
    template_name = "dashboard/networks_summary.html"

    def __init__(self):
        user = get_current_user()
        if user is None:
            user = User.objects.get(id=1)
        self.user = user
        if user.is_superuser:
            networks_count = Members.objects.all().values('network__id', 'network__network_group__name').annotate(networks_count=Count('network'))
        else:
            networks_group = user.organization.networks.all()
            networks_count = Members.objects.filter(network__in=networks_group).values('network__id', 'network__network_group__name').annotate(networks_count=Count('network'))

        self.networks_count = {}
        self.networks_summary = []
        for net_count in networks_count:
            if net_count['network__network_group__name']:
                net_name = net_count['network__network_group__name']
            else:
                net_name = 'Ungroup'

            try:
                self.networks_count[net_name]['total'] += net_count['networks_count']
            except KeyError:
                self.networks_count[net_name] = {
                        'total': net_count['networks_count'],
                        'baa': 0,
                        'invoice': 0
                        }

            member_baa = Members.objects.filter(network__id=net_count['network__id']).exclude(upload_baa__in=['', None]).count()
            self.networks_count[net_name]['baa'] += member_baa


            member_invoice = Members.objects.filter(network__id=net_count['network__id']).exclude(invoice_number__isnull=True).count()
            self.networks_count[net_name]['invoice'] += member_invoice

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['settings'] = settings
        context['user'] = self.user
        context['networks'] = self.networks_count

        return context
