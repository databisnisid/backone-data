from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from networks.models import Networks
from .models import Members, MemberLink
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


@override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
class ExternalOrgScopeTest(TestCase):
    """Regression: `External Network`/`External` must be org-scoped, not all-rows.
    They were previously in the all-rows predicate, leaking every org's sites and
    networks. Cites SPEC §I RBAC map."""

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient

        g = Group.objects.get_or_create(name="External Network")[0]

        self.net_a = Networks.objects.create(name="NetA", network_id="NA")
        self.net_b = Networks.objects.create(name="NetB", network_id="NB")
        self.org_a = Organizations.objects.create(name="OrgA")
        self.org_a.networks.add(self.net_a)
        self.org_b = Organizations.objects.create(name="OrgB")
        self.org_b.networks.add(self.net_b)

        self.mine = Members.objects.create(
            name="Mine", member_id="MA", network=self.net_a
        )
        self.theirs = Members.objects.create(
            name="Theirs", member_id="MB", network=self.net_b
        )

        self.user = User.objects.create_user(
            username="ext", password="pass1234", organization=self.org_a
        )
        self.user.groups.add(g)
        self.other = User.objects.create_user(
            username="other", password="pass1234", organization=self.org_b
        )

        from django.test import Client

        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.sess = Client()
        self.sess.force_login(self.user)

    def test_predicate_denies_external_network(self):
        from .rbac import sees_all_sites
        self.assertFalse(sees_all_sites(self.user))

    def test_sites_list_org_scoped(self):
        r = self.api.get("/api/members/sites/")
        self.assertEqual(r.status_code, 200)
        ids = {row["member_id"] for row in r.json()["results"]}
        self.assertEqual(ids, {"MA"})

    def test_networks_list_org_scoped(self):
        r = self.api.get("/api/networks/")
        self.assertEqual(r.status_code, 200)
        names = {row["name"] for row in r.json()["results"]}
        self.assertEqual(names, {"NetA"})

    def test_legacy_feed_ignores_url_user_id(self):
        # Was an IDOR: passing other's id returned other's sites.
        r = self.sess.get(f"/api/members/get_by_user/{self.other.id}/")
        self.assertEqual(r.status_code, 200)
        ids = {row["member_id"] for row in r.json()}
        self.assertEqual(ids, {"MA"})

    def test_group_member_sites_detail_org_scoped(self):
        # Groups are a global taxonomy, but member_sites_detail leaked every
        # org's site NAMES to any authed reader.
        from networks.models import NetworksGroup
        g = NetworksGroup.objects.create(name="G")
        g.member_sites.add(self.mine, self.theirs)
        r = self.api.get("/api/networks/groups/")
        self.assertEqual(r.status_code, 200)
        rows = r.json()["results"] if isinstance(r.json(), dict) else r.json()
        gid = next(row for row in rows if row["id"] == g.id)
        names = {m["name"] for m in gid["member_sites_detail"]}
        self.assertEqual(names, {"Mine"})
        self.assertEqual(gid["sites"], 1)


class LookupApiTest(TestCase):
    """T38/T41: superuser-only lookup CRUD. Cites V37,V38,V39,V43,V44."""

    def setUp(self):
        from rest_framework.test import APIClient
        from .models import SdwanPackage, BaaStatus, LinkRole

        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username="admin", password="pass1234"
        )
        self.staff = User.objects.create_user(
            username="staff", password="pass1234", is_staff=True
        )
        self.plain = User.objects.create_user(
            username="plain", password="pass1234"
        )
        # name-unique (V38); migration 0012 seeds rows via get_or_create,
        # so use get_or_create here to avoid UNIQUE collision ("Lite"/"New Link"/"MAIN").
        self.sdwan, _ = SdwanPackage.objects.get_or_create(name="Lite")
        self.baa, _ = BaaStatus.objects.get_or_create(name="New Link")
        self.role, _ = LinkRole.objects.get_or_create(name="MAIN")


    @staticmethod
    def _url(kind, pk=None):
        base = f"/api/members/lookups/{kind}/"
        return base if pk is None else f"{base}{pk}/"

    def test_superuser_can_list_all_kinds(self):
        self.client.force_authenticate(user=self.superuser)
        for kind in ("sdwan", "baa", "role"):
            r = self.client.get(self._url(kind))
            self.assertEqual(r.status_code, 200)
            # DRF PageNumberPagination default → {count, results:[...]}
            row = r.data["results"][0]
            self.assertIn("id", row)
            self.assertIn("name", row)
    def test_superuser_can_create_and_rename(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.post(self._url("sdwan"), {"name": "Pro"}, format="json")
        self.assertEqual(r.status_code, 201)
        pk = r.data["id"]
        r = self.client.patch(self._url("sdwan", pk), {"name": "Pro Max"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["name"], "Pro Max")

    def test_non_superuser_denied(self):
        # staff-not-superuser must NOT pass (V43: IsAdminUser would leak)
        for user in (self.staff, self.plain):
            self.client.force_authenticate(user=user)
            r = self.client.get(self._url("sdwan"))
            self.assertEqual(r.status_code, 403)

    def test_unaauthenticated_denied(self):
        r = self.client.get(self._url("sdwan"))
        self.assertEqual(r.status_code, 401)

    def test_duplicate_name_rejected(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.post(self._url("sdwan"), {"name": "Lite"}, format="json")
        self.assertEqual(r.status_code, 400)  # V38 unique

    def test_no_delete_route(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.delete(self._url("sdwan", self.sdwan.pk))
        self.assertIn(r.status_code, (404, 405))  # V39/V44 no destroy


class MemberCodeSalesRbacTest(TestCase):
    """T42/T43: member_code (Kode Situs) is Sales-writable on synced, denied for other roles. Cites V5,V20."""

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient

        self.client = APIClient()
        org = Organizations.objects.create(name="Org")
        net = Networks.objects.create(name="Net", network_id="NET1")
        org.networks.add(net)
        self.sales = User.objects.create_user(username="sales1", password="pass1234", organization=org)
        self.sales.groups.add(Group.objects.get_or_create(name="Sales")[0])
        self.finance = User.objects.create_user(username="fin1", password="pass1234", organization=org)
        self.finance.groups.add(Group.objects.get_or_create(name="Finance")[0])
        self.site = Members.objects.create(name="Synced Site", member_id="S1", is_manual=False, network=net)

    def test_sales_can_write_member_code_on_synced(self):
        # V5/V20: member_code is a feature field (in WRITE_BY_ROLE["Sales"]),
        # so the is_manual=False core gate must NOT reject it.
        self.client.force_authenticate(user=self.sales)
        r = self.client.patch(
            f"/api/members/sites/{self.site.pk}/", {"member_code": "SLS-001"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.site.refresh_from_db()
        self.assertEqual(self.site.member_code, "SLS-001")

    def test_finance_cannot_write_member_code_on_synced(self):
        # member_code NOT in Finance's writable set → role-level denial (V5).
        self.client.force_authenticate(user=self.finance)
        r = self.client.patch(
            f"/api/members/sites/{self.site.pk}/", {"member_code": "FIN-001"}, format="json"
        )
        self.assertEqual(r.status_code, 400)


class ProviderFilterTest(TestCase):
    """T54: provider filter on /sites. Cites C41,V56."""

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient
        from .models import LinkRole

        self.api = APIClient()
        self.role, _ = LinkRole.objects.get_or_create(name="MAIN")

        self.net_a = Networks.objects.create(name="NetA", network_id="NA")
        self.net_b = Networks.objects.create(name="NetB", network_id="NB")
        self.org_a = Organizations.objects.create(name="OrgA")
        self.org_a.networks.add(self.net_a)
        self.org_b = Organizations.objects.create(name="OrgB")
        self.org_b.networks.add(self.net_b)

        # Site with TWO TELKOM links — V56 duplication trap.
        self.double = Members.objects.create(
            name="Double", member_id="D1", network=self.net_a
        )
        for sid in ("S1", "S2"):
            MemberLink.objects.create(
                sid=sid, member=self.double, role=self.role, provider="TELKOM"
            )
        self.icon_site = Members.objects.create(
            name="IconSite", member_id="I1", network=self.net_a
        )
        MemberLink.objects.create(
            sid="S3", member=self.icon_site, role=self.role, provider="ICON"
        )
        self.bare = Members.objects.create(
            name="Bare", member_id="B1", network=self.net_a
        )
        # Another org's site, provider name must not leak into org A's options.
        self.foreign = Members.objects.create(
            name="Foreign", member_id="F1", network=self.net_b
        )
        MemberLink.objects.create(
            sid="S4", member=self.foreign, role=self.role, provider="BIZNET"
        )
        # Blank provider row — must never become a filter option.
        MemberLink.objects.create(
            sid="S5", member=self.bare, role=self.role, provider=""
        )

        self.user = User.objects.create_user(
            username="orga", password="pass1234", organization=self.org_a
        )
        self.user.groups.add(Group.objects.get_or_create(name="External")[0])
        self.api.force_authenticate(self.user)

    @staticmethod
    def _ids(response):
        return {row["member_id"] for row in response.json()["results"]}

    def test_single_provider_matches(self):
        r = self.api.get("/api/members/sites/", {"provider": ["ICON"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._ids(r), {"I1"})

    def test_two_links_same_provider_returned_once(self):
        # V56: a bare reverse-FK join would emit D1 twice.
        r = self.api.get("/api/members/sites/", {"provider": ["TELKOM"]})
        self.assertEqual(r.status_code, 200)
        rows = r.json()["results"]
        self.assertEqual([row["member_id"] for row in rows].count("D1"), 1)

    def test_providers_or_within_dimension(self):
        r = self.api.get("/api/members/sites/", {"provider": ["TELKOM", "ICON"]})
        self.assertEqual(self._ids(r), {"D1", "I1"})

    def test_tanpa_link_selects_sites_with_no_links(self):
        # B1 carries a blank-provider link row → it HAS a link, so the sentinel
        # must not pick it up; membership is by row existence, not by value.
        Members.objects.create(name="NoLinks", member_id="N1", network=self.net_a)
        r = self.api.get("/api/members/sites/", {"provider": ["Tanpa Link"]})
        self.assertEqual(self._ids(r), {"N1"})

    def test_tanpa_link_ors_with_named_provider(self):
        Members.objects.create(name="NoLinks", member_id="N1", network=self.net_a)
        r = self.api.get("/api/members/sites/", {"provider": ["Tanpa Link", "ICON"]})
        self.assertEqual(self._ids(r), {"I1", "N1"})

    def test_empty_selection_is_noop(self):
        r = self.api.get("/api/members/sites/", {"provider": []})
        self.assertEqual(self._ids(r), {"D1", "I1", "B1"})

    def test_composes_with_search(self):
        r = self.api.get(
            "/api/members/sites/", {"provider": ["TELKOM", "ICON"], "search": "Icon"}
        )
        self.assertEqual(self._ids(r), {"I1"})

    def test_providers_options_scoped_to_own_org(self):
        r = self.api.get("/api/members/sites/providers/")
        self.assertEqual(r.status_code, 200)
        # "Tanpa Link" sentinel always offered; BIZNET belongs to another org.
        self.assertEqual(r.json(), ["ICON", "TELKOM", "Tanpa Link"])

    def test_superuser_options_see_all_providers(self):
        boss = User.objects.create_superuser(username="boss", password="pass1234")
        r = self._client_for(boss).get("/api/members/sites/providers/")
        # Blank-provider row is not an option.
        self.assertEqual(r.json(), ["BIZNET", "ICON", "TELKOM", "Tanpa Link"])

    def _client_for(self, user):
        from rest_framework.test import APIClient

        c = APIClient()
        c.force_authenticate(user)
        return c


class ProviderBreakdownTest(TestCase):
    """T55: provider breakdown on the dashboard. Cites C42-C49,V57."""

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient
        from .models import LinkRole

        self.api = APIClient()
        self.role, _ = LinkRole.objects.get_or_create(name="MAIN")

        self.net_a = Networks.objects.create(name="NetA", network_id="NA")
        self.net_b = Networks.objects.create(name="NetB", network_id="NB")
        self.org_a = Organizations.objects.create(name="OrgA")
        self.org_a.networks.add(self.net_a)
        self.org_b = Organizations.objects.create(name="OrgB")
        self.org_b.networks.add(self.net_b)

        # Two links on ONE site: B8 counts distinct SITES per provider, so
        # TELKOM reads 1 for `double` despite 2 link rows (V56/T54 agree).
        self.double = Members.objects.create(
            name="Double", member_id="D1", network=self.net_a
        )
        for sid in ("S1", "S2"):
            MemberLink.objects.create(
                sid=sid, member=self.double, role=self.role, provider="TELKOM"
            )
        self.icon_site = Members.objects.create(
            name="IconSite", member_id="I1", network=self.net_a
        )
        MemberLink.objects.create(
            sid="S3", member=self.icon_site, role=self.role, provider="ICON"
        )
        # One site holding BOTH providers — the prod shape (B8) whose two
        # links the footer "titik berprovider" must collapse to one site.
        self.mixed = Members.objects.create(
            name="Mixed", member_id="M1", network=self.net_a
        )
        for provider in ("ICON", "TELKOM"):
            MemberLink.objects.create(
                sid=f"M-{provider}",
                member=self.mixed,
                role=self.role,
                provider=provider,
            )
        # No link at all -> the Tanpa Link row.
        self.bare = Members.objects.create(
            name="Bare", member_id="B1", network=self.net_a
        )
        # Another org's provider must not appear in org A's breakdown.
        self.foreign = Members.objects.create(
            name="Foreign", member_id="F1", network=self.net_b
        )
        MemberLink.objects.create(
            sid="S4", member=self.foreign, role=self.role, provider="BIZNET"
        )

        self.user = User.objects.create_user(
            username="breakdown", password="pass1234", organization=self.org_a
        )
        self.user.groups.add(Group.objects.get_or_create(name="External")[0])
        self.api.force_authenticate(self.user)

    def _rows(self, user=None):
        client = self.api
        if user is not None:
            client = self._client_for(user)
        r = client.get("/api/members/sites/stats/")
        self.assertEqual(r.status_code, 200)
        return r.json()["provider_breakdown"]

    def test_counts_distinct_sites_not_link_rows(self):
        # B8: distinct SITES per provider. `double` holds two TELKOM links and
        # counts once (V56/T54 agree); `mixed` holds ICON+TELKOM and counts
        # once under each name.
        rows = {r["provider"]: r["count"] for r in self._rows()}
        self.assertEqual(rows["TELKOM"], 2)  # double + mixed, not 3 rows
        self.assertEqual(rows["ICON"], 2)  # icon_site + mixed

    def test_unlinked_row_is_the_complement_not_a_null_join(self):
        # Partition over org A: 4 sites - 3 carrying a link = 1 bare site.
        rows = {r["provider"]: r["count"] for r in self._rows()}
        self.assertEqual(rows["Tanpa Link"], 1)

    def test_providers_descending_and_no_link_pinned_last(self):
        rows = self._rows()
        # Both names tie at 2, so provider ascending breaks it (C47).
        self.assertEqual([r["provider"] for r in rows], ["ICON", "TELKOM", "Tanpa Link"])

    def test_scoped_to_own_org(self):
        names = [r["provider"] for r in self._rows()]
        self.assertNotIn("BIZNET", names)

    def test_superuser_sees_all_orgs(self):
        boss = User.objects.create_superuser(username="boss2", password="pass1234")
        rows = {r["provider"]: r["count"] for r in self._rows(boss)}
        self.assertEqual(rows["BIZNET"], 1)
        self.assertEqual(rows["TELKOM"], 2)
        self.assertEqual(rows["ICON"], 2)

    def _client_for(self, user):
        from rest_framework.test import APIClient

        c = APIClient()
        c.force_authenticate(user)
        return c


class ProviderBreakdownStatusTest(TestCase):
    """B7+T57: named provider rows count ACTIVE sites only (matching the
    `/sites` grid default) while `Tanpa Link` is the complement against the
    FULL role set, so it agrees with the `Total Situs` card.

    Cites C50,V58,V59. Prod shape: a dismantled site holding provider links
    while an active namesake holds none, so the full role set read
    TELKOM=2/ICON=2 where /sites showed 1/1.
    """

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient
        from .models import LinkRole

        self.api = APIClient()
        self.role, _ = LinkRole.objects.get_or_create(name="MAIN")
        self.net = Networks.objects.create(name="NetS", network_id="NS")
        self.org = Organizations.objects.create(name="OrgS")
        self.org.networks.add(self.net)

        yesterday = timezone.now() - timedelta(days=1)
        # Dismantled site carrying both providers — invisible on /sites.
        self.old = Members.objects.create(
            name="Old", member_id="OLD1", network=self.net, offline_at=yesterday
        )
        # Active site carrying both providers — the only one /sites shows.
        self.new = Members.objects.create(
            name="New", member_id="NEW1", network=self.net
        )
        for site in (self.old, self.new):
            for provider in ("TELKOM", "ICON"):
                MemberLink.objects.create(
                    sid=f"{site.member_id}-{provider}",
                    member=site,
                    role=self.role,
                    provider=provider,
                )
        # One active bare site (counts) and one dismantled bare site (must not).
        Members.objects.create(name="BareActive", member_id="BA1", network=self.net)
        Members.objects.create(
            name="BareOld", member_id="BO1", network=self.net, offline_at=yesterday
        )

        self.user = User.objects.create_user(
            username="status", password="pass1234", organization=self.org
        )
        self.user.groups.add(Group.objects.get_or_create(name="External")[0])
        self.api.force_authenticate(self.user)

    def _rows(self):
        r = self.api.get("/api/members/sites/stats/")
        self.assertEqual(r.status_code, 200)
        return {x["provider"]: x["count"] for x in r.json()["provider_breakdown"]}

    def test_dismantled_site_does_not_inflate_provider_counts(self):
        # Full role set would say 2/2; active-only says 1/1 (the /sites default).
        rows = self._rows()
        self.assertEqual(rows["TELKOM"], 1)
        self.assertEqual(rows["ICON"], 1)

    def test_dismantled_site_without_links_lands_in_tanpa_link(self):
        # T57: a dismantled site holds no CURRENT link, so it has no provider
        # and belongs to the complement. Only `new` (active + linked) is
        # excluded, so 4 sites - 1 = 3.
        self.assertEqual(self._rows()["Tanpa Link"], 3)


class SitesStatusScopeTest(TestCase):
    """T58: the `/sites` list spans ALL statuses by default (C52/C53), while
    `?status=active` stays an explicit opt-in (V25) and export stays
    active-only (C55).

    Cites C52,C53,C55,V25.
    """

    def setUp(self):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient

        self.api = APIClient()
        self.net = Networks.objects.create(name="NetZ", network_id="NZ")
        self.org = Organizations.objects.create(name="OrgZ")
        self.org.networks.add(self.net)

        yesterday = timezone.now() - timedelta(days=1)
        # Prod shape: a dismantled site (3704) and an active namesake.
        self.old = Members.objects.create(
            name="Cirebon Dismantled", member_id="SIAB9101",
            network=self.net, address="CPI Cirebon", offline_at=yesterday,
        )
        self.new = Members.objects.create(
            name="Semarang Active", member_id="SIAB9102", network=self.net,
        )

        self.user = User.objects.create_user(
            username="scope", password="pass1234", organization=self.org
        )
        self.user.groups.add(Group.objects.get_or_create(name="External")[0])
        self.api.force_authenticate(self.user)

    @staticmethod
    def _ids(response):
        return {row["member_id"] for row in response.json()["results"]}

    def test_default_list_includes_dismantled_site(self):
        # C52: no ?status= param at all — the dismantled site MUST appear.
        r = self.api.get("/api/members/sites/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._ids(r), {"SIAB9101", "SIAB9102"})

    def test_search_finds_dismantled_site(self):
        # C53: searched scope is the same all-status scope.
        r = self.api.get("/api/members/sites/", {"search": "Cirebon"})
        self.assertEqual(self._ids(r), {"SIAB9101"})

    def test_status_active_is_explicit_opt_in(self):
        # V25: narrowing is still reachable, just no longer the default.
        r = self.api.get("/api/members/sites/", {"status": "active"})
        self.assertEqual(self._ids(r), {"SIAB9102"})

    def test_status_dismantle_returns_only_dismantled(self):
        r = self.api.get("/api/members/sites/", {"status": "dismantle"})
        self.assertEqual(self._ids(r), {"SIAB9101"})

    def test_export_stays_active_only(self):
        # C55: the XLSX download deliberately diverges from the grid.
        import io
        from openpyxl import load_workbook

        r = self.api.get("/api/members/sites/export/")
        self.assertEqual(r.status_code, 200)
        ws = load_workbook(io.BytesIO(r.content)).active
        ids = {str(c.value) for row in ws.iter_rows() for c in row}
        self.assertNotIn("SIAB9101", ids)
        self.assertIn("SIAB9102", ids)
