from django.test import TestCase
from networks.models import Networks
from members.models import Members
from .models import MembersDpi, MembersStarlink


class ProxyModelTest(TestCase):
    """T7: Tests for proxy model filtering. Cites V11."""

    def setUp(self):
        self.network = Networks.objects.create(name="N", network_id="N1")
        Members.objects.create(
            name="DPI Site", member_id="M1", network=self.network,
            quota_string="10GB/50GB/30/dpi"
        )
        Members.objects.create(
            name="Starlink Site", member_id="M2", network=self.network,
            quota_string="5GB/20GB/15/starlink"
        )
        Members.objects.create(
            name="Plain Site", member_id="M3", network=self.network,
            quota_string="8GB/40GB/25/plain"
        )

    def test_dpi_proxy_filters_correctly(self):
        qs = MembersDpi.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().member_id, 'M1')

    def test_starlink_proxy_filters_correctly(self):
        qs = MembersStarlink.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().member_id, 'M2')

    def test_dpi_does_not_include_starlink(self):
        self.assertFalse(MembersDpi.objects.filter(member_id='M2').exists())

    def test_starlink_does_not_include_dpi(self):
        self.assertFalse(MembersStarlink.objects.filter(member_id='M1').exists())
