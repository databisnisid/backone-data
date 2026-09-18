from django.db import transaction
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
from openpyxl import Workbook, load_workbook
from .models import Members, MemberLink
from .serializers import MemberSerializer, MemberFileSerializer, MemberLinkSerializer
from .rbac import CORE_EDIT_FIELDS, readable_fields, writable_fields, sees_all_sites
from rest_framework.permissions import BasePermission
from .models import (
    BaaStatus,
    DEFAULT_SDWAN_PACKAGE,
    LinkProvider,
    LinkRole,
    Links,
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


class ProviderLookupViewSet(_LookupViewSetBase):
    queryset = LinkProvider.objects.all()
    serializer_class = _make_lookup_serializer(LinkProvider)


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
        .values_list("provider__name", flat=True)
        .distinct()
        .order_by("provider__name")
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
            Exists(
                MemberLink.objects.filter(
                    member=OuterRef("pk"), provider__name__in=named
                )
            )
        )
    if NO_LINK in providers:
        clauses.append(~Exists(MemberLink.objects.filter(member=OuterRef("pk"))))
    predicate = clauses[0]
    for clause in clauses[1:]:
        predicate |= clause
    return qs.filter(predicate)

NO_GROUP = "Tanpa Group"  # C67 sentinel: sites in no group by either leg


def group_legs(lookup, value):
    """The ONE definition of group membership — C66/V68.

    A site belongs to a group through the network FK OR the direct M2M.
    `lookup` is the suffix applied to each leg (`"name"`, `"name__in"`,
    `"pk"`), so the filter, the dashboard card and `/networks`' own
    `NetworksGroupSerializer.get_sites` all resolve membership through this
    one expression rather than three copies that can drift.
    """
    return Q(**{f"network__network_group__{lookup}": value}) | Q(
        **{f"network_groups__{lookup}": value}
    )


# Resolved membership is an `Exists()` predicate on the site's pk, NOT a filter
# joining `network_groups`: that M2M join returns one row per matched
# attachment, so a site attached through both legs would multiply rows and
# inflate the C13 page count and `total_sites`. EXISTS only asks whether such a
# row exists, so duplicates are structurally impossible — no `.distinct()`.


def _named_group_exists(names):
    """`Exists()` predicate: the site sits in any of `names` (C66/V68)."""
    return Exists(
        Members.objects.filter(group_legs("name__in", names), pk=OuterRef("pk"))
    )


def _ungrouped_exists():
    """`Exists()` predicate: the site sits in no group by either leg (C67)."""
    return Exists(
        Members.objects.filter(group_legs("isnull", False), pk=OuterRef("pk"))
    )


def group_members_filter(qs, name):
    """The sites of `qs` in group `name` (C66/V68)."""
    return qs.filter(_named_group_exists([name]))


def ungrouped_filter(qs):
    """The sites of `qs` in NO group by either leg — the sentinel (C67,V69).

    Complement against the same scope, so this and "in at least one group"
    partition the role set exactly.
    """
    return qs.filter(~_ungrouped_exists())


def apply_group_filter(qs, groups):
    """?group=A&group=B on the sites list — C65, C66, V70.

    Selections OR within the group dimension; the sentinel ORs in like any
    other name.
    """
    # V56/V70: an empty selection is a no-op, never an empty grid. Blank values
    # are dropped too, so a stray `?group=` cannot mean "sites with no group".
    groups = [g for g in groups if g]
    if not groups:
        return qs
    named = [g for g in groups if g != NO_GROUP]
    clauses = []
    if named:
        clauses.append(_named_group_exists(named))
    if NO_GROUP in groups:
        clauses.append(~_ungrouped_exists())
    predicate = clauses[0]
    for clause in clauses[1:]:
        predicate |= clause
    return qs.filter(predicate)


def group_names(qs):
    """Group names present in `qs`, both legs, row-derived (C68)."""
    names = set(
        qs.exclude(network__network_group__isnull=True).values_list(
            "network__network_group__name", flat=True
        )
    )
    names.update(
        qs.exclude(network_groups__isnull=True).values_list("network_groups__name", flat=True)
    )
    return sorted(names)


def group_options(user):
    """Distinct group names over the caller's OWN sites (C68,V72).

    Never `NetworksGroup.objects`: a tenant sees only the groups its own sites
    belong to, an empty group is absent (2 in prod), and no other org's group
    name can surface.
    """
    return group_names(member_queryset_for(user))


def group_counts(scope, now):
    """Per-group counters, sentinel pinned last (C22,C66,C67,V69).

    A site attached through both legs belongs to both groups, matching
    `/networks`; that is a partition of the role set only in the sense that
    `sum(total_sites) == total_sites` for the sentinel-plus-named split,
    because `Tanpa Group` is the complement of `_IN_ANY_GROUP`.

    ponytail: one aggregate query per group plus one for the sentinel — 14
    groups in prod, so ~15 queries per `stats` call. Collapse into a single
    union query if the group count or dashboard load grows.
    """

    def counts(qs):
        return qs.aggregate(
            total_sites=Count("id"),
            baa_sites=Count("id", filter=~Q(upload_baa="")),
            invoice_sites=Count(
                "id", filter=~Q(invoice_number__isnull=True) & ~Q(invoice_number="")
            ),
            dismantle_sites=Count(
                "id", filter=Q(offline_at__isnull=False) & Q(offline_at__lte=now)
            ),
        )

    rows = [
        {"network_group": name, **counts(group_members_filter(scope, name))}
        for name in group_names(scope)
    ]
    rows.append({"network_group": NO_GROUP, **counts(ungrouped_filter(scope))})
    return rows

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
        {"provider": row["provider__name"], "count": row["n"]}
        for row in MemberLink.objects.filter(member__in=active)
        .exclude(provider__isnull=True)
        .values("provider__name")
        .annotate(n=Count("member", distinct=True))
        .order_by("-n", "provider__name")
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


SITES_COLUMNS = {
    "member id": "member_id",
    "name": "name",
    "member code": "member_code",
    "address": "address",
    "online at": "online_at",
    "offline at": "offline_at",
    "service line": "service_line",
    "ip address": "ip_address",
    "sdwan package": "sdwan_package",
    "baa status category": "baa_status_category",
    "invoice number": "invoice_number",
    "notes": "notes",
}
LINKS_COLUMNS = {
    "member id": "member_id",
    "link id": "link_id",
    "role": "role",
    "service": "service",
    "provider": "provider",
    "cid": "capacity",
    "sid": "sid",
}
CONTEXT_COLUMNS = ("online_at", "offline_at")

C75_IMPORT_SHEETS = (
    ("Sites", SITES_COLUMNS, ("member_id",)),
    ("Links", LINKS_COLUMNS, ("member_id", "role", "service", "provider")),
)


def _cell(value):
    """openpyxl gives a blank cell as None; every other value is a real cell (C74)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _parse_workbook(upload, problems):
    """Read the uploaded workbook into per-sheet header maps plus raw rows.

    Returns (sheets, rows) where missing sheets yield empty maps, so a file
    without `Links` simply imports nothing there. A missing required header is
    a file-level problem (V77) — it may never be treated as "every cell blank".
    """
    if upload is None:
        problems.append({"sheet": "-", "row": 0, "message": "No file uploaded."})
        return {}, []
    try:
        wb = load_workbook(upload, data_only=True)
    except Exception as exc:
        problems.append({"sheet": "-", "row": 0, "message": "Unreadable workbook: %s" % exc})
        return {}, []
    sheets = {}
    rows = []
    for name, spec, required in C75_IMPORT_SHEETS:
        ws = wb[name] if name in wb.sheetnames else None
        header_index = {}
        if ws is not None:
            for idx, header in enumerate(next(ws.iter_rows(max_row=1, values_only=True), ())):
                mapped = spec.get(str(header).strip().lower(), "")
                if mapped:
                    header_index[idx] = mapped
            for field in required:
                if field not in header_index.values():
                    problems.append(
                        {
                            "sheet": name,
                            "row": 1,
                            "message": "Missing required column: %s"
                            % field.replace("_", " ").title(),
                        }
                    )
        sheets[name] = header_index
    if problems:
        return sheets, rows
    for name, _spec, _required in C75_IMPORT_SHEETS:
        ws = wb[name] if name in wb.sheetnames else None
        if ws is None:
            continue
        header_index = sheets[name]
        fields = set(header_index.values())
        for number, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            cells = {}
            for idx, field in header_index.items():
                cells[field] = _cell(values[idx]) if idx < len(values) else None
            if any(v is not None for v in cells.values()):
                rows.append(
                    {"sheet": name, "row": number, "fields": fields, "cells": cells}
                )
    return sheets, rows

def _messages(errors):
    return "; ".join("%s: %s" % (k, " ".join(map(str, v))) for k, v in errors.items())

def _links_and_lookup(user):
    """Caller's existing links by id, plus the valid lookup names (C71/V74)."""
    links = {
        link.id: link
        for link in MemberLink.objects.filter(member__in=member_queryset_for(user))
    }
    return links, {
        "role": {r.name for r in LinkRole.objects.all()},
        "provider": {p.name for p in LinkProvider.objects.all()},
    }


def _stage_site(entry, member, request, allowed, writes, problems):
    cells = entry["cells"]
    fields = entry["fields"]
    payload = {}
    for field in SITES_COLUMNS.values():
        # An absent column leaves the field untouched (C74/V77). Member ID is
        # the row key, not content; the timeline columns belong to the upstream
        # sync, never to Excel.
        if field == "member_id" or field in CONTEXT_COLUMNS:
            continue
        if field not in allowed or field not in fields:
            continue
        value = cells.get(field)
        if value in (None, ""):
            # C74: a blank optional cell clears the stored value. `notes` is
            # the one column whose model field is non-null, so it clears to "".
            payload[field] = "" if field == "notes" else None
        else:
            payload[field] = value
    if not member.is_manual:
        # V75: a core column on a synced site is skipped silently — never
        # compared against the DB, never rejected — because a plain superuser
        # export carries Name/Address/Service Line on every row.
        payload = {f: v for f, v in payload.items() if f not in CORE_EDIT_FIELDS}
    if not payload:
        return 0
    serializer = MemberSerializer(member, data=payload, partial=True, context={"request": request})
    if not serializer.is_valid():
        problems.append(
            {"sheet": "Sites", "row": entry["row"], "message": _messages(serializer.errors)}
        )
        return 0

    def current(field):
        value = getattr(member, field)
        return value.name if field in ("sdwan_package", "baa_status_category") and value else value

    changed = [f for f, v in payload.items() if (current(f) or "") != (v or "")]
    if not changed:
        return 0
    writes.append(serializer.save)
    return len(changed)


def _stage_link(entry, member, request, lookup, links, writes, problems):
    cells = entry["cells"]
    row_problem = {
        "sheet": "Links",
        "row": entry["row"],
    }
    link_id = cells.get("link_id")
    instance = None
    if link_id not in (None, ""):
        try:
            link_id = int(float(link_id))
        except (TypeError, ValueError):
            problems.append({**row_problem, "message": "Link ID is not a number: %s" % link_id})
            return 0
        instance = links.get(link_id)
        if instance is None or instance.member_id != member.id:
            problems.append(
                {
                    **row_problem,
                    "message": "Link ID %s does not belong to Member ID %s."
                    % (link_id, cells["member_id"]),
                }
            )
            return 0
    # C74/V77: `Role`/`Service`/`Provider` are required on a NEW link, but a
    # blank cell on an EXISTING one clears it to NULL — all three columns are
    # nullable, and the export writes a blank cell whenever a legacy link has
    # none. A name that resolves to nothing still rejects on either row.
    for field in ("role", "service", "provider"):
        value = cells.get(field)
        if value in (None, ""):
            if instance is None:
                problems.append({**row_problem, "message": "%s is required." % field.title()})
                return 0
            continue
        if field == "provider":
            if value not in lookup["provider"]:
                problems.append({**row_problem, "message": "Unknown Provider: %s" % value})
                return 0
        elif field == "role":
            if value not in lookup["role"]:
                problems.append({**row_problem, "message": "Unknown Role: %s" % value})
                return 0
        else:
            # `Links.name` carries no DB uniqueness, so a name must resolve to
            # exactly one service row — 0 or 2+ matches reject rather than
            # guess (C71/V74).
            services = list(Links.objects.filter(name=value)[:2])
            if len(services) != 1:
                problems.append({**row_problem, "message": "Unknown Service: %s" % value})
                return 0
            cells["service"] = services[0].pk
    payload = {field: cells.get(field) or None for field in ("role", "provider")}
    payload["service"] = cells.get("service") or None
    for column in ("capacity", "sid"):
        # C74: a blank optional cell clears, but a column absent from the file
        # leaves the stored value alone (`value == ""` on both paths).
        if column in entry["fields"]:
            payload[column] = cells.get(column) or ""
    serializer = MemberLinkSerializer(
        instance, data=payload, partial=True, context={"request": request}
    )
    if not serializer.is_valid():
        problems.append({**row_problem, "message": _messages(serializer.errors)})
        return 0
    if instance is None:
        writes.append(lambda: serializer.save(member=member))
        return len(payload)
    current = {
        "role": instance.role.name if instance.role else "",
        "service": instance.service_id,
        "provider": instance.provider.name if instance.provider else "",
        "capacity": instance.capacity or "",
        "sid": instance.sid or "",
    }
    changed = [f for f, v in payload.items() if (v or "") != (current[f] or "")]
    if not changed:
        return 0
    writes.append(serializer.save)
    return len(changed)


def _apply_workbook(request, upload):
    """Validate an uploaded workbook; returns (problems, changed, rows, writes).

    `writes` holds the only side effects of the whole import: preview ignores
    it (V76 — preview writes nothing), apply runs it inside one
    `transaction.atomic()` after this same check has come back clean.
    """
    problems = []
    _sheets, rows = _parse_workbook(upload, problems)
    if problems:
        return problems, {}, [], []
    user = request.user
    allowed = writable_fields(user)
    links, lookup = _links_and_lookup(user)
    changed = {"Sites": 0, "Links": 0}
    changed_rows = []
    writes = []
    sites = {}
    for entry in rows:
        member_id = entry["cells"].get("member_id")
        if member_id in (None, ""):
            problems.append(
                {"sheet": entry["sheet"], "row": entry["row"], "message": "Member ID is required."}
            )
            continue
        member = sites.get(member_id)
        if member is None:
            member = member_queryset_for(user).filter(member_id=member_id).first()
            if member is None:
                problems.append(
                    {
                        "sheet": entry["sheet"],
                        "row": entry["row"],
                        "message": "Unknown Member ID: %s" % member_id,
                    }
                )
                continue
            sites[member_id] = member
        if entry["sheet"] == "Sites":
            n = _stage_site(entry, member, request, allowed, writes, problems)
        else:
            n = _stage_link(entry, member, request, lookup, links, writes, problems)
        changed[entry["sheet"]] += n
        if n:
            changed_rows.append([entry["sheet"], entry["row"], n])
    return problems, changed, changed_rows, writes


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
            qs = apply_group_filter(qs, self.request.query_params.getlist("group"))
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
        qs = apply_group_filter(
            member_queryset_for(request.user), request.query_params.getlist("group")
        )
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
        # C65/V71: the header picker's own option list comes from THIS payload,
        # so `group_aggregates` is deliberately computed over the org scope
        # rather than the narrowed `qs` — otherwise selecting one group would
        # erase every other group from the dropdown (T71: no second fetch).
        groups = group_counts(member_queryset_for(request.user), now)
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
                "group_aggregates": groups,
                "provider_breakdown": provider_breakdown(qs),
                "sdwan_breakdown": sdwan_breakdown(qs),
            }
        )

    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        """Return the lookup option lists (sdwan/baa/role/provider names) for the FE selects (C25,C61)."""

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
                "provider": list(
                    LinkProvider.objects.order_by("name").values_list("name", flat=True)
                ),
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

    @action(detail=False, methods=["get"], url_path="groups")
    def groups(self, request):
        """Distinct group names the caller's own sites belong to (C67,C68,V72).

        Scoped by member_queryset_for — a tenant never learns another org's
        group names. The C67 sentinel is appended so ungrouped sites stay
        reachable (9 of 1270 prod sites).
        """
        return Response(group_options(request.user) + [NO_GROUP])

    @action(detail=False, methods=["get"], url_path="export", url_name="export-xlsx")
    def export(self, request):
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

        # C71/V74: one row per installed link of the exported sites, keyed
        # `Member ID` + `Link ID`; `Lookup` lists the names import accepts.
        # NOTE: `.iterator()` yields no `_result_cache`, so `Member ID` must
        # come from the map collected during the loop below.
        exported = {}
        for m in qs.iterator(chunk_size=500):
            network_name = m.network.name if m.network else ""
            network_group = m.network_group() or ""
            exported[m.id] = m.member_id
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

        links_ws = wb.create_sheet("Links")
        links_ws.append(["Member ID", "Link ID", "Role", "Service", "Provider", "CID", "SID"])
        links = (
            MemberLink.objects.filter(member_id__in=exported)
            .select_related("role", "service", "provider")
            .order_by("id")
        )
        for link in links:
            links_ws.append(
                [
                    exported.get(link.member_id, ""),
                    link.id,
                    link.role.name if link.role else "",
                    link.service.name if link.service else "",
                    link.provider.name if link.provider else "",
                    link.capacity or "",
                    link.sid or "",
                ]
            )

        lookup_ws = wb.create_sheet("Lookup")
        lookup_ws.append(["Kind", "Name"])
        for role in LinkRole.objects.order_by("name"):
            lookup_ws.append(["Role", role.name])
        for service in Links.objects.order_by("name"):
            lookup_ws.append(["Service", service.name])
        for provider in LinkProvider.objects.order_by("name"):
            lookup_ws.append(["Provider", provider.name])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="sites.xlsx"'
        wb.save(response)
        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="import/preview",
        url_name="import-preview",
        permission_classes=[IsAuthenticated, IsSuperUser],
    )
    def import_preview(self, request):
        """V76: report every problem and change count, write nothing."""
        problems, changed, rows, _writes = _apply_workbook(request, request.FILES.get("file"))
        body = {"problems": problems, "changed": changed, "rows": rows}
        return Response(body, status=400 if problems else 200)

    @action(
        detail=False,
        methods=["post"],
        url_path="import/apply",
        url_name="import-apply",
        permission_classes=[IsAuthenticated, IsSuperUser],
    )
    def import_apply(self, request):
        """V76: re-validate the same upload, then write it in one transaction."""
        problems, changed, rows, writes = _apply_workbook(request, request.FILES.get("file"))
        body = {"problems": problems, "changed": changed, "rows": rows}
        if problems:
            return Response(body, status=400)
        with transaction.atomic():
            for write in writes:
                write()
        return Response(body)

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
