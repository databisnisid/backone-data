import requests
from unittest.mock import patch, MagicMock
from django.test import TestCase
from .models import Networks
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
