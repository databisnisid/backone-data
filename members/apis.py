from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from django.http import HttpResponse
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from openpyxl import Workbook
from .models import Members, MemberLink
from .serializers import MemberSerializer, MemberFileSerializer, MemberLinkSerializer
from .rbac import readable_fields, writable_fields, sees_all_sites
from rest_framework.permissions import BasePermission
from .models import (
    BaaStatus,
    DEFAULT_SDWAN_PACKAGE,
    LinkRole,
    MemberLink,
    Members,
    SdwanPackage,
)


class IsSuperUser(BasePermission):
    """Superuser-only gate (C28,V37,V43). NOT IsAdminUser — that checks
    is_staff, so a staff-but-not-superuser Wagtail admin would gain access."""

    message = "Superuser only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


def _make_lookup_serializer(model):
    class _LookupSerializer(serializers.ModelSerializer):
        class Meta:
            fields = ("id", "name")

    _LookupSerializer.Meta.model = model  # bind via Meta attr (closure NameError)
    _LookupSerializer.__name__ = f"{model.__name__}Serializer"
    return _LookupSerializer


class _LookupViewSetBase(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.UpdateModelMixin,
):
    """Shared lookup CRUD (T38). No DestroyModelMixin + http_method_names
    excludes delete → no DELETE route exists (V39,V44). Custom IsSuperUser
    permission gates every method (V37,V43)."""

    permission_classes = [IsAuthenticated, IsSuperUser]
    lookup_field = "id"
    # V44: structurally no delete (no DestroyModelMixin; http_method_names
    # omits "delete" so the router can't mount a delete route either).
    http_method_names = ["get", "post", "put", "patch", "head", "options"]


class SdwanLookupViewSet(_LookupViewSetBase):
    queryset = SdwanPackage.objects.all()
    serializer_class = _make_lookup_serializer(SdwanPackage)


class BaaLookupViewSet(_LookupViewSetBase):
    queryset = BaaStatus.objects.all()
    serializer_class = _make_lookup_serializer(BaaStatus)


class RoleLookupViewSet(_LookupViewSetBase):
    queryset = LinkRole.objects.all()
    serializer_class = _make_lookup_serializer(LinkRole)


def member_queryset_for(user):
    """Full role-set queryset (active + dismantled) — aggregates/detail never double-filter (V25)."""
    if sees_all_sites(user):
        qs = Members.objects.all()
    elif user.organization is None:
        return Members.objects.none()
    else:
        networks = user.organization.networks.all()
        qs = Members.objects.filter(network__in=networks)
    return qs.order_by("id")


def active_members_queryset(qs):
    now = timezone.now()
    return qs.filter(Q(offline_at__isnull=True) | Q(offline_at__gt=now))


def apply_status_filter(qs, status):
    """?status=active | all (default) | dismantle on the sites list — V25, C52."""
    if status == "dismantle":
        return qs.filter(offline_at__isnull=False, offline_at__lte=timezone.now())
    if status == "active":
        return active_members_queryset(qs)
    return qs  # "all" or unknown → full role set


NO_LINK = "Tanpa Link"  # C41 sentinel: sites with zero MemberLink rows


def link_providers(user):
    """Distinct non-empty providers over the caller's own scoped sites (C41/V56).

    Scoped by member_queryset_for so a tenant never learns another org's
    provider names from the dropdown.
    """
    return list(
        MemberLink.objects.filter(member__in=member_queryset_for(user))
        .exclude(provider__isnull=True)
        .exclude(provider="")
        .values_list("provider", flat=True)
        .distinct()
        .order_by("provider")
    )


def apply_provider_filter(qs, providers):
    """?provider=A&provider=B on the sites list — C41, V56.

    Selections OR within the provider dimension. Exists() (not a bare
    reverse-FK join) so a site with two matching links appears once.
    """
    # V56: empty selection is a no-op, never an empty grid. Blank values are
    # dropped too, so a stray `?provider=` cannot mean "sites with no links".
    providers = [p for p in providers if p]
    if not providers:
        return qs
    named = [p for p in providers if p != NO_LINK]
    clauses = []
    if named:
        clauses.append(
            Exists(MemberLink.objects.filter(member=OuterRef("pk"), provider__in=named))
        )
    if NO_LINK in providers:
        clauses.append(~Exists(MemberLink.objects.filter(member=OuterRef("pk"))))
    predicate = clauses[0]
    for clause in clauses[1:]:
        predicate |= clause
    return qs.filter(predicate)


def provider_breakdown(qs):
    """Distinct-site counts per provider over the viewer's role scope (C51/V57).

    Named rows count DISTINCT ACTIVE sites (C50/V58): a site holding two links
    from the same provider counts once, and a dismantled site contributes no
    current provider — both match the `/sites` grid and its T54/V56 filter.
    Blank/null providers are excluded, matching link_providers(), so the panel
    and the C41 dropdown agree on what a name is.

    `Tanpa Link` is the complement against the FULL role set (V59), so the
    panel partitions the `Total Situs` card: a dismantled site holds no current
    link, hence no provider, hence no link. Never
    filter(member_links__isnull=True) — that join double-counts a site with
    several links (V57).
    """
    active = active_members_queryset(qs)
    rows = [
        {"provider": row["provider"], "count": row["n"]}
        for row in MemberLink.objects.filter(member__in=active)
        .exclude(provider__isnull=True)
        .exclude(provider="")
        .values("provider")
        .annotate(n=Count("member", distinct=True))
        .order_by("-n", "provider")
    ]
    linked = active.filter(
        Exists(MemberLink.objects.filter(member=OuterRef("pk")))
    ).count()
    rows.append({"provider": NO_LINK, "count": qs.count() - linked})
    return rows

def sdwan_breakdown(qs):
    """Distinct-site counts per SDWAN package over the viewer's ACTIVE scope (C58/V61).

    sdwan_package is a forward FK, single-valued per site, so a plain grouping
    partitions the active set exactly — no DISTINCT-site hazard like the
    reverse-FK link join in V56, and no complement row is needed because C59
    backfills every NULL onto the `Tanpa SDWAN` row.
    """
    return [
        {"package": row["sdwan_package__name"], "count": row["n"]}
        for row in active_members_queryset(qs)
        .exclude(sdwan_package__isnull=True)
        .values("sdwan_package__name")
        .annotate(n=Count("id", distinct=True))
        .order_by("-n", "sdwan_package__name")
    ]


def apply_sdwan_filter(qs, package):
    """?sdwan=<name> on the sites list — C58, V62.

    Exact match on the package name, composing with the other filters rather
    than replacing them. A blank value is a no-op (mirroring V56); an unknown
    name legitimately returns an empty grid.
    """
    if not package:
        return qs
    return qs.filter(sdwan_package__name=package)


class SitesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MemberSerializer
    lookup_field = "pk"
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name", "member_id", "member_code", "address")
    ordering_fields = ("id", "name", "member_id", "online_at", "offline_at")

    def get_queryset(self):
        qs = member_queryset_for(self.request.user)
        if self.action == "list":
            qs = apply_status_filter(qs, self.request.query_params.get("status", "all"))
            # Filter by network IDs when ?network= is present (V34 site picker).
            nets = self.request.query_params.getlist("network")
            if nets:
                qs = qs.filter(network_id__in=nets)
            qs = apply_provider_filter(qs, self.request.query_params.getlist("provider"))
            qs = apply_sdwan_filter(qs, self.request.query_params.get("sdwan"))
        return qs

    def create(self, request, *args, **kwargs):
        if not sees_all_sites(request.user):
            raise PermissionDenied("Only Support/superuser may create manual sites.")
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], url_path="upload")
    def upload(self, request, pk=None):
        site = self.get_object()
        serializer = MemberFileSerializer(
            site, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        site.refresh_from_db()
        out = MemberSerializer(site, context={"request": request})
        return Response(out.data)
    FILE_FIELD_NAMES = {"upload_baa", "po_file_user", "po_file_vendor", "invoice_file", "bap_file"}

    @action(detail=True, methods=["post"], url_path="delete-file")
    def delete_file(self, request, pk=None):
        site = self.get_object()
        field_name = request.data.get("field")
        if field_name not in self.FILE_FIELD_NAMES:
            return Response({"detail": "Invalid field name."}, status=400)
        setattr(site, field_name, None)
        site.save(update_fields=[field_name])
        site.refresh_from_db()
        out = MemberSerializer(site, context={"request": request})
        return Response(out.data)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = member_queryset_for(request.user)
        now = timezone.now()
        total = qs.count()
        online = active_members_queryset(qs).count()
        offline = total - online
        manual = qs.filter(is_manual=True).count()
        # C60/V63: every network holding >=1 site, no [:10] slice — the card
        # shows 10 and hides the rest behind a collapsible trigger. A network
        # with zero sites stays out (the card is a ranking over total_sites,
        # a site count), so the payload sums to `total` exactly.
        nets = (
            qs.exclude(network__isnull=True)
            .values("network_id", "network__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        groups = (
            qs.exclude(network__network_group__isnull=True)
            .values("network__network_group__name")
            .annotate(
                total=Count("id"),
                baa=Count("id", filter=~Q(upload_baa="")),
                invoice=Count("id", filter=~Q(invoice_number__isnull=True) & ~Q(invoice_number="")),
                dismantle=Count("id", filter=Q(offline_at__isnull=False) & Q(offline_at__lte=now)),
            )
            .order_by("network__network_group__name")
        )
        return Response(
            {
                "total_sites": total,
                "online_sites": online,
                "offline_sites": offline,
                "manual_sites": manual,
                "top_networks": [
                    {
                        "id": n["network_id"],
                        "name": n["network__name"],
                        "sites": n["count"],
                    }
                    for n in nets
                ],
                "group_aggregates": [
                    {
                        "network_group": g["network__network_group__name"],
                        "total_sites": g["total"],
                        "baa_sites": g["baa"],
                        "invoice_sites": g["invoice"],
                        "dismantle_sites": g["dismantle"],
                    }
                    for g in groups
                ],
                "provider_breakdown": provider_breakdown(qs),
                "sdwan_breakdown": sdwan_breakdown(qs),
            }
        )
    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        """Return the lookup option lists (sdwan/baa/role names) for the FE selects (C25)."""
        from .models import SdwanPackage, BaaStatus, LinkRole

        return Response(
            {
                "sdwan_package": list(
                    SdwanPackage.objects.order_by("name").values_list("name", flat=True)
                ),
                # C59: the FE preselects this instead of hardcoding the name.
                "default_sdwan_package": DEFAULT_SDWAN_PACKAGE,
                "baa_status_category": list(
                    BaaStatus.objects.order_by("name").values_list("name", flat=True)
                ),
                "role": list(LinkRole.objects.order_by("name").values_list("name", flat=True)),
            }
        )

    @action(detail=False, methods=["get"], url_path="providers")
    def providers(self, request):
        """Distinct link providers the caller's own sites carry (C41,V56).

        Scoped by member_queryset_for — a tenant never learns another org's
        provider names. The C41 sentinel is appended so zero-link sites stay
        reachable (1226 of 1228 prod sites).
        """
        return Response(link_providers(request.user) + [NO_LINK])

    @action(detail=False, methods=["get"], url_path="export", url_name="export-xlsx")
    def export(self, request):
        from django.utils import timezone as tz
        qs = apply_status_filter(
            self.get_queryset(), self.request.query_params.get("status", "active")
        )
        user = request.user
        allowed = readable_fields(user)
        scalar_cols = [
            "member_id",
            "name",
            "member_code",
            "address",
            "online_at",
            "offline_at",
            "network_name",
            "network_group",
            "service_line",
        ]
        cols = [c for c in scalar_cols if c in allowed or c == "name"]
        cols += sorted(
            [
                c
                for c in allowed
                if c
                in (
                    "ip_address",
                    "sdwan_package",
                    "project_number",
                    "baa_status_category",
                    "invoice_number",
                    "notes",
                )
            ]
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Sites"
        ws.append([c.replace("_", " ").title() for c in cols])

        for m in qs.iterator(chunk_size=500):
            network_name = m.network.name if m.network else ""
            network_group = m.network_group() or ""
            is_online = "Online"
            if m.offline_at is None:
                is_online = "Online"
            elif m.offline_at >= tz.now():
                is_online = "Online"
            else:
                is_online = "Offline"
            row = {
                "member_id": m.member_id,
                "name": m.name,
                "member_code": m.member_code or "",
                "address": m.address or "",
                "online_at": m.online_at,
                "offline_at": m.offline_at,
                "network_name": network_name,
                "network_group": network_group,
                "service_line": m.service_line or "",
                "ip_address": m.ip_address or "",
                "sdwan_package": m.sdwan_package.name if m.sdwan_package else "",
                "project_number": m.project_number or "",
                "baa_status_category": m.baa_status_category.name if m.baa_status_category else "",
                "invoice_number": m.invoice_number or "",
                "notes": m.notes or "",
            }
            ws.append([row.get(c, "") for c in cols])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="sites.xlsx"'
        wb.save(response)
        return response

    def get_serializer_class(self):
        return MemberSerializer

class MemberLinkViewSet(viewsets.ModelViewSet):
    """Write MemberLinks on sites. Sales may create/update/delete (V24). Other roles read-only."""

    permission_classes = [IsAuthenticated]
    serializer_class = MemberLinkSerializer

    def get_queryset(self):
        qs = MemberLink.objects.filter(member__in=member_queryset_for(self.request.user))
        if self.action == "list" and "member" in self.request.query_params:
            qs = qs.filter(member_id=self.request.query_params["member"])
        return qs

    def _assert_sales_write(self):
        if "member_links" not in writable_fields(self.request.user):
            raise PermissionDenied("Only Sales may write member links.")

    def perform_create(self, serializer):
        self._assert_sales_write()
        serializer.save()

    def perform_update(self, serializer):
        self._assert_sales_write()
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_sales_write()
        instance.delete()

    @action(detail=False, methods=["get"], url_path="services")
    def services(self, request):
        """List Link (service) options for the Add-link editor — readable by any authenticated role."""
        from .models import Links
        from rest_framework import serializers

        class LinkOptionSerializer(serializers.ModelSerializer):
            class Meta:
                model = Links
                fields = ("id", "name")

        opts = LinkOptionSerializer(Links.objects.all().order_by("name"), many=True)
        return Response(opts.data)
