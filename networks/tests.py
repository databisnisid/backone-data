import requests
from unittest.mock import patch, MagicMock
from django.test import TestCase
from .models import Networks, NetworksGroup
from .utils import get_networks


class GetNetworksTest(TestCase):
    """T4: Tests for get_networks upsert + delete. Cites V2, V3, V16."""

    @patch('networks.utils.requests.get')
    def test_creates_new_networks(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {'fields': {'name': 'N1', 'description': 'd1', 'network_id': 'NET1'}},
            {'fields': {'name': 'N2', 'description': 'd2', 'network_id': 'NET2'}},
        ]
        mock_get.return_value = mock_resp

        get_networks('http://api.test')

        self.assertEqual(Networks.objects.count(), 2)
        self.assertTrue(Networks.objects.filter(network_id='NET1').exists())
        self.assertTrue(Networks.objects.filter(network_id='NET2').exists())

    @patch('networks.utils.requests.get')
    def test_updates_existing_networks(self, mock_get):
        Networks.objects.create(name='Old', network_id='NET1', description='old desc')

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {'fields': {'name': 'New', 'description': 'new desc', 'network_id': 'NET1'}},
        ]
        mock_get.return_value = mock_resp

        get_networks('http://api.test')

        n = Networks.objects.get(network_id='NET1')
        self.assertEqual(n.name, 'New')
        self.assertEqual(n.description, 'new desc')

    @patch('networks.utils.requests.get')
    def test_deletes_networks_not_in_response(self, mock_get):
        Networks.objects.create(name='Keep', network_id='NET1')
        Networks.objects.create(name='Delete', network_id='NET2')

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {'fields': {'name': 'Keep', 'description': '', 'network_id': 'NET1'}},
        ]
        mock_get.return_value = mock_resp

        get_networks('http://api.test')

        self.assertEqual(Networks.objects.count(), 1)
        self.assertTrue(Networks.objects.filter(network_id='NET1').exists())
        self.assertFalse(Networks.objects.filter(network_id='NET2').exists())

    @patch('networks.utils.requests.get')
    def test_api_failure_does_not_delete(self, mock_get):
        Networks.objects.create(name='N1', network_id='NET1')

        mock_get.side_effect = requests.exceptions.ConnectionError('failed')

        get_networks('http://api.test')

        self.assertEqual(Networks.objects.count(), 1)

    @patch('networks.utils.requests.get')
    def test_empty_response_does_not_delete(self, mock_get):
        Networks.objects.create(name='N1', network_id='NET1')

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        get_networks('http://api.test')

        self.assertEqual(Networks.objects.count(), 1)


class NetworkGroupCrudTest(TestCase):
    """T1/T2/T4: writable NetworksGroupViewSet + superuser-only write gate. Cites V31,V32,V33."""

    def setUp(self):
        from accounts.models import User
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.superuser = User.objects.create_superuser(username="root", password="pass1234")
        self.staff = User.objects.create_user(username="staff", password="pass1234", is_staff=True)
        self.staff.groups.add(Group.objects.get_or_create(name="Sales")[0])
        self.net = Networks.objects.create(name="Net", network_id="NET1")

    def _url(self, *parts):
        base = "/api/networks/groups/"
        for p in parts:
            base += f"{p}/"
        return base

    def test_superuser_creates_group(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.post(self._url(), {"name": "G1"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(NetworksGroup.objects.filter(name="G1").exists())

    def test_superuser_renames_group(self):
        self.client.force_authenticate(user=self.superuser)
        g = NetworksGroup.objects.create(name="Old")
        r = self.client.patch(self._url(g.pk), {"name": "New"}, format="json")
        self.assertEqual(r.status_code, 200)
        g.refresh_from_db()
        self.assertEqual(g.name, "New")

    def test_staff_cannot_write_group(self):
        # V33: staff-but-not-superuser is rejected by the write gate.
        self.client.force_authenticate(user=self.staff)
        r = self.client.post(self._url(), {"name": "X"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_group_delete_orphans_networks(self):
        # V32: deleting a group SET_NULLs its networks' network_group (never deletes sites).
        self.client.force_authenticate(user=self.superuser)
        group = NetworksGroup.objects.create(name="G")
        self.net.network_group = group
        self.net.save()
        r = self.client.delete(self._url(group.pk))
        self.assertEqual(r.status_code, 204)
        self.net.refresh_from_db()
        self.assertIsNone(self.net.network_group)
        self.assertFalse(NetworksGroup.objects.filter(pk=group.pk).exists())

    def test_group_serializer_exposes_site_count(self):
        # V31: group detail includes a read-only member-site count (derived via network).
        from members.models import Members

        self.client.force_authenticate(user=self.superuser)
        group = NetworksGroup.objects.create(name="G")
        self.net.network_group = group
        self.net.save()
        Members.objects.create(name="Site", member_id="S1", is_manual=False, network=self.net)
        r = self.client.get(self._url(group.pk))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["sites"], 1)



class NetworkAssignmentTest(TestCase):
    """T1: superuser assigns a network to a group via PATCH networks/<id> network_group. Cites V31,V33."""

    def setUp(self):
        from accounts.models import User
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.superuser = User.objects.create_superuser(username="root", password="pass1234")
        self.user = User.objects.create_user(username="usr", password="pass1234")
        self.net = Networks.objects.create(name="Net", network_id="NET1")
        self.group = NetworksGroup.objects.create(name="G")

    def test_superuser_assigns_network_to_group(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.patch(f"/api/networks/{self.net.pk}/", {"network_group": self.group.pk}, format="json")
        self.assertEqual(r.status_code, 200)
        self.net.refresh_from_db()
        self.assertEqual(self.net.network_group, self.group)

    def test_nonsuper_cannot_assign_network(self):
        # V33: assignment is a write → superuser gate on non-SAFE methods.
        self.client.force_authenticate(user=self.user)
        r = self.client.patch(f"/api/networks/{self.net.pk}/", {"network_group": self.group.pk}, format="json")
        self.assertEqual(r.status_code, 403)