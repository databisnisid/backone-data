from unittest.mock import patch, MagicMock
from django.test import TestCase
from accounts.models import User, Organizations
from networks.models import Networks, NetworksGroup
from members.models import Members
from .summary_panels import NetworksPanelSummary


class NetworksPanelSummaryTest(TestCase):
    """T8: Tests for NetworksPanelSummary context. Cites V9, V10, V17."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin", password="pass1234", is_superuser=True
        )

    @patch('dashboard.summary_panels.get_current_user')
    def test_superuser_sees_all_networks(self, mock_get_user):
        mock_get_user.return_value = self.user

        net1 = Networks.objects.create(name="N1", network_id="NET1")
        net2 = Networks.objects.create(name="N2", network_id="NET2")
        Members.objects.create(name="S1", member_id="M1", network=net1)
        Members.objects.create(name="S2", member_id="M2", network=net2)

        panel = NetworksPanelSummary()
        ctx = panel.get_context_data({})

        self.assertEqual(ctx['user'], self.user)
        self.assertIn('networks', ctx)
        self.assertIsInstance(ctx['networks'], dict)

    @patch('dashboard.summary_panels.get_current_user')
    def test_normal_user_sees_org_networks_only(self, mock_get_user):
        org = Organizations.objects.create(name="Org1")
        net_in = Networks.objects.create(name="In", network_id="NETIN")
        net_out = Networks.objects.create(name="Out", network_id="NETOUT")
        org.networks.add(net_in)

        user = User.objects.create_user(
            username="u1", password="pass1234", organization=org
        )
        mock_get_user.return_value = user

        Members.objects.create(name="S1", member_id="M1", network=net_in)
        Members.objects.create(name="S2", member_id="M2", network=net_out)

        panel = NetworksPanelSummary()
        ctx = panel.get_context_data({})

        totals = sum(v['total'] for v in ctx['networks'].values())
        self.assertEqual(totals, 1)  # only org network member counted

    @patch('dashboard.summary_panels.get_current_user')
    def test_context_has_settings(self, mock_get_user):
        mock_get_user.return_value = self.user

        panel = NetworksPanelSummary()
        ctx = panel.get_context_data({})

        self.assertIn('settings', ctx)
