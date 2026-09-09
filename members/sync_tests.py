from unittest.mock import patch, MagicMock
from django.test import TestCase
from networks.models import Networks
from .models import Members
from .utils import get_members_by_net, get_members_all


class GetMembersByNetTest(TestCase):
    """T5: Tests for get_members_by_net upsert. Cites V1, V4."""

    def setUp(self):
        self.network = Networks.objects.create(name="N", network_id="NET1")

    @patch('members.utils.requests.get')
    def test_creates_new_members(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{
            "name": "Site A", "member_code": "C1", "description": "d",
            "member_id": "M1", "address": "addr", "location": "loc",
            "online_at": "2024-01-01", "offline_at": None,
            "mobile_number_first": "08123", "quota_first": "10GB/50GB/30/dpi",
        }]
        mock_get.return_value = mock_resp

        get_members_by_net('http://api.test', 'NET1')

        self.assertEqual(Members.objects.count(), 1)
        m = Members.objects.get(member_id='M1')
        self.assertEqual(m.name, 'Site A')
        self.assertEqual(m.network, self.network)

    @patch('members.utils.requests.get')
    def test_updates_existing_member(self, mock_get):
        Members.objects.create(
            name="Old", member_id="M1", network=self.network
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{
            "name": "New", "member_code": "C1", "description": "d",
            "member_id": "M1", "address": "addr", "location": "loc",
            "online_at": "2024-01-01", "offline_at": None,
            "mobile_number_first": "08123", "quota_first": "10GB/50GB/30/dpi",
        }]
        mock_get.return_value = mock_resp

        get_members_by_net('http://api.test', 'NET1')

        m = Members.objects.get(member_id='M1')
        self.assertEqual(m.name, 'New')

    @patch('members.utils.requests.get')
    def test_sync_does_not_overwrite_sales_member_code(self, mock_get):
        # V6: member_code is Sales-owned — sync must never clobber it.
        Members.objects.create(
            name="Site", member_id="M1", member_code="SALES-CODE", network=self.network
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{
            "name": "Site", "member_code": "UPSTREAM-CODE", "description": "d",
            "member_id": "M1", "address": "addr", "location": "loc",
            "online_at": "2024-01-01", "offline_at": None,
            "mobile_number_first": "08123", "quota_first": "10GB/50GB/30/dpi",
        }]
        mock_get.return_value = mock_resp

        get_members_by_net('http://api.test', 'NET1')

        m = Members.objects.get(member_id='M1')
        self.assertEqual(m.member_code, 'SALES-CODE')

    @patch('members.utils.requests.get')
    def test_members_never_deleted(self, mock_get):
        Members.objects.create(
            name="Existing", member_id="M1", network=self.network
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        get_members_by_net('http://api.test', 'NET1')

        self.assertEqual(Members.objects.count(), 1)

    def test_nonexistent_network_does_nothing(self):
        get_members_by_net('http://api.test', 'NOPE')
        self.assertEqual(Members.objects.count(), 0)


class GetMembersAllTest(TestCase):
    """Tests for get_members_all iteration. Cites V12."""

    def setUp(self):
        self.n1 = Networks.objects.create(name="N1", network_id="NET1")
        self.n2 = Networks.objects.create(name="N2", network_id="NET2")

    @patch('members.utils.get_members_by_net')
    def test_iterates_all_networks(self, mock_fn):
        get_members_all('http://api.test')

        self.assertEqual(mock_fn.call_count, 2)
        call_ids = sorted([c.args[1] for c in mock_fn.call_args_list])
        self.assertEqual(call_ids, ['NET1', 'NET2'])
