from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from networks.models import Networks
from .models import Members
from accounts.models import User, Organizations
from .views import prepare_data, randomize_coordinate, get_members_by_user


class QuotaParsingTest(TestCase):
    """T1: Tests for Members quota parsing methods. Cites V6."""

    def setUp(self):
        self.network = Networks.objects.create(
            name="Test Network", network_id="NET001"
        )

    def _make(self, quota_string):
        return Members.objects.create(
            name="Test Site",
            member_id="M001",
            network=self.network,
            quota_string=quota_string,
        )

    # --- get_quota_type ---

    def test_quota_type_returns_fourth_field(self):
        m = self._make("10GB/50GB/30/dpi")
        self.assertEqual(m.get_quota_type(), "dpi")

    def test_quota_type_empty_string(self):
        m = self._make("")
        self.assertEqual(m.get_quota_type(), "")

    def test_quota_type_none(self):
        m = self._make(None)
        self.assertEqual(m.get_quota_type(), "")

    def test_quota_type_too_few_fields(self):
        m = self._make("10GB/50GB")
        self.assertEqual(m.get_quota_type(), "")

    # --- get_quota_current ---

    def test_quota_current_returns_first_field(self):
        m = self._make("10GB/50GB/30/dpi")
        self.assertEqual(m.get_quota_current(), "10GB")

    def test_quota_current_empty(self):
        m = self._make("")
        self.assertEqual(m.get_quota_current(), "")

    # --- get_quota_usage ---

    def test_quota_usage_calculates_difference(self):
        m = self._make("10GB/50GB/30/dpi")
        self.assertEqual(m.get_quota_usage(), "40.0GB")

    def test_quota_usage_empty_string_returns_zero(self):
        m = self._make("")
        self.assertEqual(m.get_quota_usage(), "0GB")

    def test_quota_usage_none_returns_zero(self):
        m = self._make(None)
        self.assertEqual(m.get_quota_usage(), "0GB")

    def test_quota_usage_missing_total(self):
        m = self._make("10GB")
        self.assertEqual(m.get_quota_usage(), "0GB")

    # --- get_quota_day ---

    def test_quota_day_returns_third_field(self):
        m = self._make("10GB/50GB/30/dpi")
        self.assertEqual(m.get_quota_day(), "30")

    def test_quota_day_empty(self):
        m = self._make("")
        self.assertEqual(m.get_quota_day(), "")

    # --- get_quota_string_no_total ---

    def test_quota_string_no_total(self):
        m = self._make("10GB/50GB/30/dpi")
        self.assertEqual(m.get_quota_string_no_total(), "10GB/30/DPI")

    def test_quota_string_no_total_empty(self):
        m = self._make("")
        self.assertEqual(m.get_quota_string_no_total(), "")


class PrepareDataTest(TestCase):
    """T2: Tests for prepare_data WKT parsing. Cites V14, V18."""

    def setUp(self):
        self.network = Networks.objects.create(name="N", network_id="N1")

    def _member(self, location=None):
        return Members.objects.create(
            name="S", member_id="M1", network=self.network, location=location
        )

    def test_valid_wkt_parsed_correctly(self):
        """WKT in ';POINT(lng lat)' format (after semicolon split)."""
        m = self._member(location=";POINT(106.8 -6.2)")
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['lng'], '106.8')
        self.assertEqual(result[0]['lat'], '-6.2')

    def test_none_location_falls_back(self):
        m = self._member(location=None)
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(len(result), 1)
        self.assertIn('lat', result[0])
        self.assertIn('lng', result[0])

    def test_malformed_wkt_no_semicolon_falls_back(self):
        m = self._member(location="garbage")
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(len(result), 1)
        # Falls back to default location (with random offset)
        self.assertIn('lat', result[0])
        self.assertIn('lng', result[0])

    def test_empty_location_string_falls_back(self):
        m = self._member(location="")
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(len(result), 1)
        self.assertIn('lat', result[0])

    def test_empty_queryset(self):
        result = prepare_data(Members.objects.none())
        self.assertEqual(result, [])

    def test_randomize_coordinate_shifts_duplicates(self):
        members = [
            {'lat': '-6.2', 'lng': '106.8', 'id': 1, 'name': 'A'},
            {'lat': '-6.2', 'lng': '106.8', 'id': 2, 'name': 'B'},
        ]
        result = randomize_coordinate(members)
        self.assertEqual(len(result), 2)

    def test_member_fields_populated(self):
        m = self._member(location=";POINT(106.8 -6.2)")
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(result[0]['name'], 'S')
        self.assertEqual(result[0]['member_id'], 'M1')
        self.assertEqual(result[0]['id'], m.pk)


class OnlineStatusTest(TestCase):
    """T6: Tests for online/offline status. Cites V5."""

    def setUp(self):
        self.network = Networks.objects.create(name="N", network_id="N1")

    def _member(self, offline_at=None):
        return Members.objects.create(
            name="S", member_id="M1", network=self.network,
            offline_at=offline_at
        )

    def test_none_offline_at_is_online(self):
        m = self._member(offline_at=None)
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(result[0]['is_online'], 1)

    def test_future_offline_at_is_online(self):
        future = timezone.now() + timedelta(hours=1)
        m = self._member(offline_at=future)
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(result[0]['is_online'], 1)

    def test_past_offline_at_is_offline(self):
        past = timezone.now() - timedelta(hours=1)
        m = self._member(offline_at=past)
        result = prepare_data(Members.objects.filter(pk=m.pk))
        self.assertEqual(result[0]['is_online'], 0)


@override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
class OrgFilteringTest(TestCase):
    """T3: Tests for get_members_by_user org filtering. Cites V7, V15."""

    def setUp(self):
        self.network = Networks.objects.create(name="N", network_id="N1")
        self.org = Organizations.objects.create(name="Org1")
        self.org.networks.add(self.network)
        self.user = User.objects.create_user(
            username="testuser", password="pass1234",
            organization=self.org
        )
        self.superuser = User.objects.create_superuser(
            username="admin", password="pass1234"
        )
        self.member = Members.objects.create(
            name="S", member_id="M1", network=self.network
        )
        self.client.login(username="testuser", password="pass1234")

    def test_org_user_sees_org_members(self):
        response = self.client.get(
            f'/api/members/get_by_user/{self.user.id}/'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['member_id'], 'M1')

    def test_unauthenticated_returns_302(self):
        self.client.logout()
        response = self.client.get(
            f'/api/members/get_by_user/{self.user.id}/'
        )
        self.assertEqual(response.status_code, 302)

    def test_superuser_sees_all(self):
        self.client.login(username="admin", password="pass1234")
        response = self.client.get(
            f'/api/members/get_by_user/{self.superuser.id}/'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
