# SPEC.md — BackOne Data

## §G — Goal

Rework BackOne Data into full decoupled app: Next.js frontend (React 19, App Router) re-skins ALL user screens per the "Mockup Sites Dashboard" mockup; Django 5.2 DRF backend serves JSON + files; hourly `sync_data` feeds upstream-synced sites (read-only). Wagtail retired to superuser-only console at `/django-admin/`.

## §C — Constraints

| ID | Constraint |
|---|---|
| C1 | Django 5.2.17 LTS + Wagtail 7.4.3 retained at current pins — **no version bump** (blast radius) |
| C2 | DRF `djangorestframework==3.18.1` already installed — backend API surface via DRF (no new serializer framework) |
| C3 | JWT auth: `djangorestframework-simplejwt==5.5.1` (new dep). PyJWT pulled transitively |
| C4 | Next.js 16.3.4 + React 19.2.8 + TS, in monorepo `frontend/` subdir. Vite not used (Next). Tailwind for styling (mockup spec'd Tailwind) |
| C5 | Auth flow = **BFF proxy**: browser talks only to Next origin; Next `/api/*` route handlers proxy to Django DRF server-side, JWT held in httpOnly cookie. No CORS on Django, no token in JS/localStorage. `django-cors-headers` NOT required |
| C6 | Separate SPA host; Django remains backend origin. API at `/api/` on Django |
| C7 | Wagtail remains the live admin at root (`''`) — login, homepage/map dashboard, Sites/Quota/Networks/Organizations snippet menus. Stock Django admin stays at `/django-admin/`. Once SPA covers all user screens, relocate Wagtail to superuser-only `/django-admin/` mount (see T18) |
| C8 | **Sync-as-authority (amended)**: sites fed by upstream cron are **read-only for CORE/identity fields** (C11); **user-owned feature fields ARE writable** by authorized roles on synced sites — PO user, PO vendor, invoice number+file, BAA status, Kode Situs (`member_code`), `member_links` (provider/service/sid/capacity), notes. Identity/network/timeline stay immutable. Only manual sites get full core-field edits |
| C9 | Manual sites marked `Members.is_manual=True`. Distinguish manual vs synced by this flag (not by absent upstream id) |
| C10 | IP address field editable ONLY on manual sites (Support role writes it) |
| C11 | Upstream payload fields sync owns (read-only): name, address, location(WKT), online_at, offline_at, network, service_line, quota_string. Everything else is user-owned — incl. `member_code` (Sales-owned, never sync-written) |
| C12 | Uploads (BAA download for sync sites / upload for Finance-Sales / PO user / PO vendor / bukti invoice / BAP) stored in Django MEDIA, served/proxied via BFF |
| C13 | Row scale: **server-paginated** (100/page), server filter + sort + total count, server-side XLSX export. No client virtualization/AG Grid |
| C14 | RBAC retains Django Groups (Sales, Finance, Purchasing, Support, External/External Network) + org-filtering; enforced server-side in DRF, mirrored as column visibility in FE |
| C15 | Sync IS multi-domain: `config/workers.sync_data(domain_api)` runs once per upstream instance via `dockerize/cronjobs` (backone + vn lines). `get_networks` scopes its delete to rows owned by the syncing domain |
| C16 | SQLite dev / MySQL prod (existing) |
| C17 | `id-id` locale, `Asia/Jakarta` TZ |
| C18 | No CI/CD, no linter/typecheck config added (repo convention) |
| C19 | `SECRET_KEY` read from env (`os.getenv('SECRET_KEY')`, dev fallback only); JWT signed with this key — production MUST set real `SECRET_KEY` before `/api/sites/` protected endpoints deploy |

| C20 | **Purchasing** Django Group added (prod id=11, created) — writable ONLY `po_file_vendor`. Superseded by C34 (adds `project_number`) |
| C33 | **Edit form field visibility** — `service_line`, `location`, `quota_string` hidden in site edit form (read-only data, no edit needed); `network` kept but shows `network_name` (read-only, always disabled); `invoice_number` scalar field added for Finance role; all fields disabled (read-only) for non-writable roles |
| C34 | **Purchasing write scope expanded** — `project_number` added to Purchasing writable set alongside `po_file_vendor`; Purchasing can edit PO vendor + project number |
| C35 | **Support write scope narrowed** — Support restricted to `ip_address` + `member_links` only; removed: `sdwan_package`, `baa_status_category`, `upload_baa`, `invoice_number`, `invoice_file`, `po_file_user`, `po_file_vendor`, `bap_file`, `member_code`, `notes` |

| C36 | **External groups get no Quota/Networks/Pengaturan** — a user in Django Group `External` **or** `External Network` loses sidebar items `quota`, `networks`, `organizations` (title "Pengaturan") and the routes `/quota`, `/networks`, `/organizations` redirect to `/dashboard/default`. Either group wins over any other role group (hybrid `Sales`+`External` still hides); `is_superuser` wins over the group rule and always keeps all items. Menu + route only — no new API 403, `/api/*` reads stay org-filtered as today |
| C21 | **Dismantle = derived view** of `Members.offline_at != null` — no new column/status, no migration, no drift (Q3/Q7) |
| C22 | Dashboard aggregates ship **per `network_group`** (NetworksGroup): BAA = `upload_baa` non-null; Invoice = `invoice_number` non-null (Q7). Top Networks retained, dismantle count folds into Online/Offline cards |
| C23 | **File upload cap 10MB / PDF,XLS,XLSX,DOC,DOCX** (existing `MAX_UPLOAD_SIZE`+`ALLOWED_UPLOAD_EXT`, already enforced in `MemberFileSerializer`) — reused, not re-added |
| C24 | Lookup value sets (`sdwan_package`, `baa_status_category`, `MemberLink.role`) move from fixed Python choices to **DB-backed tables** — each a Wagtail snippet model mirroring `Links` (`name` CharField, delete-protect). No value removed while a site references it |
| C25 | API stays **string in/out**: `SlugRelatedField(slug_field="name")` resolves the string→lookup row on write, returns the lookup `name` string on read. FE unchanged for the *values*; the *option lists* now come from an endpoint, not hard-coded arrays |
| C26 | Seed rows (prod-distinct): SDWAN `{BackOne - SDWAN Lite, Pro, Gateway, Tanpa SDWAN}`; BAA `{New Link, Upgrade Link, Downgrade Link, Relokasi}`; role `{MAIN, BACKUP, SINGLE}`. Backfill maps existing string→row (prod has only `BackOne - SDWAN Pro`, `New Link`, `BACKUP`) |
| C27 | Migration `members.0012`: `CharField`→FK on `Members.sdwan_package`/`baa_status_category` + `MemberLink.role`; new tables seeded + backfilled in a data migration. MySQL prod |

| C28 | **Superuser-only lookup management**: FE page `/settings/lookups` + the lookup CRUD endpoints are accessible to superuser only — FE gate (`me.is_superuser`) on nav+route AND a custom DRF permission checking `request.user.is_superuser` on every endpoint method (**not** `IsAdminUser` — that gates `is_staff`, so a staff-not-superuser Wagtail admin would gain write access) (no client-side-only bypass) |
| C29 | **New DRF lookup CRUD endpoints**, not Wagtail snippet admin: `/api/lookups/{sdwan,baa,role}/` list+create and `<id>/` rename, all under a custom `IsSuperUser` permission (`is_superuser`); serializer exposes `{id, name}`. Wagtail snippet admin is HTML/CSRF, doesn't fit the JWT SPA (C5). `kind` ∈ {sdwan, baa, role} → the three models |
| C30 | **Config-only page**: `/settings/lookups` manages only the three shared value lists. Per-site assignment stays in `/sites` (existing `/api/members/options/` read), no duplicated picker |
| C31 | **One page, 3 sections**: `/settings/lookups` renders SDWAN/BAA/Role sections from a single reusable list component parameterized by `kind` — no per-table route |
| C32 | **Create + rename only, no delete** (mirrors V33 + FK `PROTECT`); rename to an existing name → 400 (unique on `name`) surfaced in UI, never silently merged |
| C37 | **Login lockout is time-based and self-healing** — 3 failed logins lock the username for `AXES_COOLOFF_TIME` (default **30 MINUTES**, env-overridable). Retrying while locked never extends it; the lockout lifts on its own once the window passes. Prod MUST set `AXES_COOLOFF_TIME=30` in the docker **service env** (unit = minutes) — the baked `.env` loses to the service env |

| ID | Ruling | Source |
|---|---|---|
| R1 | Next.js 16.3.4, React 19.2.8, React-DOM 19.2.8 = current stable | registry.npmjs.org dist-tags |
| R2 | djangorestframework-simplejwt 5.5.1 latest | pypi.org/pypi/djangorestframework-simplejwt |
| R3 | Django 6.1.1, Wagtail 8.0 are latest upstream — **deliberately NOT adopted** | pypi.org/pypi/django, pypi.org/pypi/wagtail |
| R4 | django-cors-headers 4.9.0 exists but not needed (BFF same-origin) | pypi.org |
| R5 | PHP/SMS-like `next`/`react` PyPI packages are bogus; use npm registry for FE versions | pypi.org (misleading) |

## §I — Interfaces

### URL surfaces

| Origin | Route | Target | Purpose |
|---|---|---|---|
| Django | `/api/auth/token/` | SimpleJWT TokenObtainPairView | Login → access+refresh |
| Django | `/api/auth/token/refresh/` | SimpleJWT TokenRefreshView | Rotate refresh |
| Django | `/api/sites/` | DRF ViewSet | List (paginated, filter, sort) |
| Django | `/api/sites/<id>/` | DRF ViewSet | Detail / update manual-only |
| Django | `/api/sites/<id>/files/` | DRF upload endpoint | BAA/PO/BAP/invoice file upload |
| Django | `/api/sites/export.xlsx` | DRF export | Server-side XLSX |
| Django | `/api/members/options/` | DRF ViewSet action | Lookup options for the three dropdowns (sdwan/baa/role), string list — feeds FE selects (C25) |

| Django | `/api/lookups/{kind}/` | DRF ViewSet | List + create lookup values for `kind` ∈ {sdwan,baa,role} — `IsAdminUser` (C28,C29) |
| Django | `/api/lookups/{kind}/<id>/` | DRF ViewSet | Rename a lookup value (PATCH) — `IsAdminUser` (C29,C32) |
| Next | `/settings/lookups` | Next page | Superuser-only lookup config page (C28,C30,C31) |
| Django | `/api/networks/`, `/api/organizations/` | DRF ViewSets | Read-only lists for selects/menus |
| Django | `/` (root) | Wagtail admin (`include(wagtailadmin_urls)`) | Live admin: login + homepage/map dashboard + snippet menus (C7) |
| Django | `/django-admin/` | Stock Django admin | Superuser-only debug/bootstrap console (C7) |
| Next | `/app/` | Next pages | SPA UI (login, sites grid, settings) |
| Next | `/api/auth/...`, `/api/proxy/...` | Next route handlers | BFF proxy — log in token, hold JWT httpOnly, proxy Django calls |

### Existing DB tables (reused, `members` is authority)

`members` keep: `id, name, member_code, description, member_id(uq), address, location(WKT), online_at(Date), offline_at, network FK, links M2M, upload_baa, invoice_number, notes, service_line, quota_string, created_at, updated_at`.

Keep `networks`, `networks_group`, `links`, `organizations`, `auth_user`, Django groups as-is.

### New model fields (mockup cols A–I → existing `members` + new tables)
| Mockup col | Field / model | RW scope (C8/C9/C10/C12) |
|---|---|---|
| A Situs & Address | `member_code`, `address` (exist); **`ip_address`** (new) | ip_address: manual-only |
| B SDWAN pkg | **`sdwan_package`** FK→ SDWAN snippet (real table, C24); value returned as string (C25) | editable manual |
| B Project no. | **`project_number`** | editable manual |
| B Networks | `network` FK (auto) | read-only |
| B multi-link | **new child `MemberLink`** (ParentalKey→Members via ClusterableModel): `role` FK→ role snippet (C24), `service` FK→Links, `provider` CharField, `capacity` CharField, `sid` CharField | editable manual; links on synced read-only |
| C Timeline | `online_at`, `offline_at` (exist) | read-only on sync |
| D Status BAA | **`baa_status_category`** FK→ BAA snippet (C24); string in/out (C25) | editable manual; on synced only Support/…masked |
| D BAA file | `upload_baa` (exist) | upload: synced read-only, manual editable |
| E PO | **`po_file_user`**, **`po_file_vendor`** FileFields (new) | upload manual/Finance |
| F Invoice | `invoice_number` (exist); **`invoice_file`** FileField (new) | Finance |
| G Dismantle | **`bap_file`** FileField (new) | Support |
| H Notes | `notes` (exist) | editable manual |

`MemberLink`: ParentalKey to Members so ClusterableModel inline M2M survives Wagtail snippets (if ever surfaced) — keeps modelcluster dependency.

### RBAC map (DRF permission + FE visibility)

| Role / Group | Sites grid | Edit | Files upload | Export | Notes |
|---|---|---|---|---|---|
| Superuser | all | all (manual+synced core) | all | yes | full |
| Support | all (unmasked cols) | manual: `ip_address`, `member_links` | BAA download | yes | creates manual sites |
| Sales | org | `member_code`, `sdwan_package`, `baa_status_category`, `member_links`, `upload_baa`, `po_file_user` | PO user, BAA | yes | write-on-synced (C8) |
| Finance | org | `invoice_number`, `invoice_file` | invoice file | yes | isolated |
| Purchasing | org | `po_file_vendor`, `project_number` | PO vendor | yes | new group (C20) |
| External / External Network | org (already visible) | no | BAA download | no | read-only map + sites; sidebar omits Quota/Networks/Pengaturan and those 3 routes redirect (C36) |

### Cron

Two lines, one per upstream instance (`dockerize/cronjobs`), both baked into the image at `/etc/crontabs/root`:

```
0 * * * * python /app/manage.py shell --command "from config.workers import sync_data; sync_data('https://manage.backone.cloud')"
0 * * * * python /app/manage.py shell --command "from config.workers import sync_data; sync_data('https://manage.vn.backone.cloud')"
```

Domain-keyed by `Networks.domain` = `urlparse(domain_api).netloc`. Prereq: the `backone-data-crond` service MUST NOT mount the `backone-data-app` volume over `/app` — that volume shadowed `/app` with 2025-10-27 code, so cron silently ran pre-fix sync until the mount was removed (`docker service update --mount-rm /app backone-data-crond`).

## §V — Invariants

| ID | Invariant |
|---|---|
| V1 | `Members.member_id` unique; sync upserts by it (existing) |
| V2 | `Networks.network_id` unique; sync upserts by it (existing) |
| V3 | Sync never deletes Members — upsert only (existing) |
| V4 | `Members.is_manual=True` ⟺ site created via "Tambah Situs Baru"; synced sites `is_manual=False` |
| V5 | **Write-scope rule (amended)**: CORE/identity fields immutable on synced sites (`is_manual=False`) — update/delete/upload of those blocked server-side. **Feature/user-owned fields ARE writable on synced** by authorized roles (C8): `po_file_user`, `po_file_vendor`, `invoice_number`, `invoice_file`, `baa_status_category`, `member_links`, `member_code` (Kode Situs, Sales-owned), notes. FE shows view mode for core, edit mode for permitted feature fields |
| V6 | Sync writes only C11-whitelisted fields; never writes `is_manual`, `ip_address`, `sdwan_package`, `project_number`, `po_file_*`, `bap_file`, `invoice_file`, `baa_status_category`, notes, `member_code` (Sales-owned — sync must not clobber) |
| V7 | `baa_status_category` one of 4 fixed choices; `sdwan_package` one of 4 fixed choices. **Enforced at DRF serializer boundar** (ChoiceField) — NOT at `Members.save()`/model level (modelcluster `create` skips `full_clean`; verified `sdwan_package="Nope"` accepted via `.save()`). All production writes go through DRF serializers, so enforcement is the trust boundary there |
| V8 | Manual sites can exist without an upstream `network` (nullable network for manual-only) or attach to existing network — network required for synced |
| V9 | File fields are server-validated (extension/content check: PDF primarily); size cap |
| V10 | `Members.delete()` also deletes all attached files (extend existing `upload_baa` delete to new file fields — existing V10) |
| V11 | API auth required on every /api/ route (DRF `IsAuthenticated`) |
| V12 | Org filtering: non-superuser sees only own org's networks+members — enforced in DRF querysets |
| V13 | XLSX export honors the same RBAC/org filter as list view (no data leak) |
| V14 | BFF holds JWT only in httpOnly + Secure cookie; never exposed to JS |
| V15 | Refresh token rotates; reuse detection invalidates (SimpleJWT default) |
| V16 | `quota_string` parsing methods (existing V6/V17) unchanged — reused by Quota read-only module |
| V17 | Online status preserved: `is_online=1` iff `offline_at IS NULL` OR `offline_at >= now()` (existing) |
| V18 | WKT `location` parse fallback preserved (existing V14/V18) |
| V19 | Manual-site creation default: `is_manual=True`; cannot be converted to synced |
| V20 | **Synced-site write gate**: `MemberSerializer.update()` + `MemberFileSerializer.update()` relax the `is_manual` guard to check each proposed field — allow feature field if in role's `writable_fields`, deny CORE/identity fields on synced. No blanket synced-write (V5). `member_code` is a feature field (in `FEATURE_FIELDS`), so it passes the synced gate once a role holds it in `writable_fields` |
| V22 | **Dismantle derived**: dismantle set = `Members.offline_at IS NOT NULL`. No `status`/`dismantle_at` column. Count = filter, not stored |
| V23 | **Purchasing RBAC (superseded by C34/V47)**: Original `WRITE_BY_ROLE["Purchasing"] = {"po_file_vendor"}` now expanded to `{"po_file_vendor", "project_number"}` per grill (C34). `READ_EXTRA_BY_ROLE` includes both. Org-filtered like Sales/Finance (`_is_authorized_all` unchanged — not in Support/External all-rows set) |
| V24 | **Nested MemberLink write path**: `member_links` is a writable nested serializer, not `read_only=True`; create/update/delete of links flows through DRF + `save_child_instances` on `Members.save()` — never a raw modelcluster bypass that skips a role/field check. Sales may write links on synced + manual; other roles link read-only |
| V25 | **Dismantled-site visibility**: `offline_at <= now` (dismantled) sites remain READ + summarizable for role-filtered users (Sales/Finance/Purchasing) — allows PO/invoice fill on dismantled sites and correct per-group dismantle counts. Only the default "active sites" list filters them out; aggregates + detail must not double-filter (BLOCK-2 fix) |



| V26 | **Site table fits viewport** — `/sites` list renders without horizontal scroll on desktop; the Action ("Ubah") column is visible without scrolling. Columns compress/truncate cell content (never drop a column) so the last column stays on-screen |
| V27 | **No global top-header search** — `(main)` shell header shows sidebar toggle + page title only; SearchDialog command palette (trigger button + ⌘J palette) not rendered in any `(main)` page. Per-page search (sites list "Pencarian sites...") unaffected |
| V28 | **No sidebar Quick Create/Inbox row** — `(main)` app sidebar opens directly on the nav-groups block; the primary "Quick Create" button + adjacent Inbox button are not rendered in any sidebar state (expanded or icon-collapsed). Nav groups/routes unchanged |

| V37 | **Lookup CRUD is superuser-only end to end**: `/api/lookups/*` methods are under a custom `IsSuperUser` permission checking `request.user.is_superuser` (write AND read) — **not** `IsAdminUser` (that gates `is_staff`, so a staff-not-superuser Wagtail admin would gain access). `/settings/lookups` route + sidebar item gate on `me.is_superuser`. A non-superuser calling the API directly gets 403 — FE gate is cosmetic, DRF is the boundary (C28) |
| V38 | **Lookup `name` DB-unique per table** — `unique=True` on `SdwanPackage.name`, `BaaStatus.name`, `LinkRole.name` (new migration). Duplicate create/rename → 400 (DB unique + serializer validation) surfaced as an inline error, never merged or silently deduped. Guarantees `SlugRelatedField` never hits `MultipleObjectsReturned` (guards the V32 read path for `/sites`) (C32) |
| V39 | **Lookup CRUD never deletes, structurally** — `LookupViewSet` extends `GenericViewSet` + `List`/`Create`/`Update` mixins (or `http_method_names` excluding `delete`), so no `DELETE` route exists to call. Values are add/rename only; removing an in-use value is impossible (FK `PROTECT`) and no endpoint exposes it (V33) |
| V40 | **`/api/members/options/` stays the FE read source for `/sites`** — the new `/api/lookups/*` list is a separate superuser-only surface; the `/sites` selects keep pulling from `/api/members/options/` (C25,V31). No FE dropdown regressions |
| V41 | **Lookup nav + route gate on `me.is_superuser`, plumbed end to end** — `getCurrentUser()` (main layout) includes `is_superuser`; sidebar rendering filters the `/settings/lookups` item out unless `is_superuser`; `/settings/lookups` route redirects non-superusers to `/dashboard/default`. A non-superuser sees no nav entry and cannot reach the route (C28) |
| V43 | **Superuser permission is `is_superuser`, not `IsAdminUser`** — a custom permission class (e.g. `IsSuperUser`) checks `request.user.is_superuser`; DRF `IsAdminUser` (gates `is_staff`) is NOT used, else a staff-not-superuser Wagtail admin gains lookup write access (C28,C29) |
| V44 | **No DELETE route is exposed** — the view is built from mixins that exclude destroy (or `http_method_names` omits `delete`), and the router/URL conf never mounts a destroy route, so deletion is structurally impossible (C32) |
| V30 | **Login left panel shows random photo** — desktop login left panel (`lg:w-1/3`, previously `bg-primary`) renders a random photo from `picsum.photos` as background instead of the flat black/primary color; BackOne logo + "BackOne Data" title stay overlaid and legible (translucent dark scrim behind the text). Mobile (`<lg`) panel stays hidden |
| V31 | Lookup tables are the sole source of SDWAN/BAA/role options — no hard-coded choice arrays remain in backend models or FE `data.ts`. **FE dropdowns load options from `/api/members/options/`**, not a static list |
| V32 | `sdwan_package`/`baa_status_category`/`role` resolve string→FK server-side on write (`SlugRelatedField(slug_field="name")`), emit the lookup `name` string on read (C25). A value not in the table is rejected (serializer `SlugRelatedField` validation), preserving V7's serializer-boundary enforcement |
| V33 | Lookup tables delete-protect (`user_can_delete_obj=False`, like `Links`); deleting an in-use value is impossible (C24) |
| V34 | Migration `members.0012` is data-safe: seed rows, backfill existing strings→rows (prod has `BackOne - SDWAN Pro`, `New Link`, `BACKUP` only), then `CharField`→FK. No data loss, no orphan FKs (C27) |
| V35 | **Export + sites-list read emit the lookup name string** — `apis.py` XLSX export rows and the sites-list read-builder must emit `m.sdwan_package.name` / `m.baa_status_category.name` (or empty) — the cells/cards render the value, not `<SdwanPackage: ...>` (guards the `sites-view.tsx` Badge + export cell) |
| V36 | **`MemberLink.__str__` emits the role name** — `models.py` `__str__` `"%s" % self.role` on an FK renders `<LinkRole: MAIN>`; the serializer read path + `__str__` must emit `self.role.name` (or empty) so Wagtail and link rows show `MAIN`/`BACKUP`/`SINGLE` |
| V45 | **Edit form hidden/display fields** — `service_line`, `location`, `quota_string` not rendered in site edit form (C33). `network` kept as read-only disabled field displaying `network_name` via `ScalarDef.displayFor` (not raw PK). `invoice_number` added for Finance |
| V46 | **Support write scope** (C35): `WRITE_BY_ROLE["Support"] = {"ip_address", "member_links"}` on both backend `members/rbac.py` and frontend `data.ts` WRITE_BY_ROLE. Support can add IP + links on manual sites only. Removed from Support: `sdwan_package`, `baa_status_category`, `upload_baa`, `invoice_number`, `invoice_file`, `po_file_user`, `po_file_vendor`, `bap_file`, `member_code`, `notes` |
| V47 | **Purchasing write scope** (C34): `WRITE_BY_ROLE["Purchasing"] = {"po_file_vendor", "project_number"}` on both backend `members/rbac.py` and frontend `data.ts`. Purchasing can edit PO vendor + project number |
| V48 | **Sales write scope** (C8): `WRITE_BY_ROLE["Sales"] = {"baa_status_category", "upload_baa", "notes", "member_links", "member_code", "sdwan_package", "po_file_user"}` on both backend `members/rbac.py` and frontend `data.ts`. Sales can edit SDWAN package, BAA status, PO user, links, Kode Situs, BAA upload, and notes |
| V49 | **Sync deletion is domain-scoped** — `Networks.domain` (CharField, netloc of `sync_data()`'s `domain_api`) discriminates instances. `get_networks` seeds its delete candidate list from `Networks.objects.filter(domain=domain)` only, so an id absent from one upstream's `/api/networks/list/` can NEVER delete a network owned by another upstream. Enforced by `networks/tests.py::GetNetworksTest::test_sync_of_one_domain_never_deletes_another_domains_networks` |
| V50 | **Cron runs image code, never a volume shadow** — no service may bind/volume-mount `/app` of the `backone-data` image; the crontab lives at `/etc/crontabs/root` inside the image, so a code fix reaches cron only when the crond service references the fixed image AND nothing shadows `/app`. Known ceiling: same-domain network removal still cascades to that domain's `Members` (retained `on_delete=CASCADE`), so V3 holds only cross-domain — see B5 |

| V51 | **External/External-Network nav hide is plumbed end to end** — `getCurrentUser()` (`(main)/layout.tsx`) passes `groups` from `/api/auth/me/` into `NavUserInfo`; `visibleItems()` in `app-sidebar.tsx` drops ids `quota`/`networks`/`organizations` when `groups` contains `External` or `External Network`, after the `is_superuser` branch; the three routes redirect to `/dashboard/default` under the same predicate, mirroring the V41 lookups gate. Rule is deny-only, never a grant — a group list never unlocks an item. FE gate is cosmetic: DRF read permissions and org-filtering are unchanged (C36) |
| V52 | **Axes lockout MUST expire unattended, MUST NOT be extended by retries** — `AXES_COOLOFF_TIME` is an explicit `timedelta` (read as MINUTES; a bare int/float is HOURS to django-axes, so the old `2` silently meant 2 hours); `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False`, so an attempt made while locked — including one carrying the CORRECT password — never rewrites `attempt_time`/`failures_since_start` and never restarts the window. Enforced by `accounts/tests.py::AxesLockoutTest` (C37) |

| ID | Status | Task | Cites |
|---|---|---|---|
| T1 | ✅ | Backend: deps `djangorestframework-simplejwt==5.5.1` + `drf-spectacular==0.30.0` in requirements.txt; wire SimpleJWT auth + Swagger/OpenAPI (`/api/schema/`, `/api/docs/`) | C3 |
| T2 | ✅ | Backend: migrate `Members` + new fields; new `MemberLink` model; `is_manual` default False; nullable network guard | V4,V6,V8 |
| T3 | ✅ | Backend: DRF auth wiring (SimpleJWT login/refresh endpoints, `IsAuthenticated`) | C3,V11 |
| T4 | ✅ | Backend: `SitesViewSet` list (server pagination + filter + sort + total count), detail (read-only auto), update manual-only | V5, C13 |
| T5 | ✅ | Backend: RBAC permission class (Sales/Finance/Support/External org filtering + field-level write gate) | C14,V12 |
| T6 | ✅ | Backend: file upload/serve endpoint (BAA/PO user/vendor/invoice/BAP), MEDIA storage, validation, delete cascade on member delete | C12,V9,V10 |
| T8 | ✅ | Backend: Quota + Networks + Organizations read-only ViewSets | C13 |
| T9 | ✅ | FE: scaffold `frontend/` from `arhamkhnz/next-shadcn-admin-dashboard` (Next 16 + React 19 + TS + Tailwind v4 + shadcn/Base UI + TanStack Table v9, config-driven RBAC, auth/unauthorized screens); `npm ci` + `next build` proven | C4 |
| T10 | ✅ | FE: BFF auth flow — Next route handlers `/api/auth/{login,logout,refresh,me}` + data proxy `/api/backend/[...path]`; JWT in httpOnly cookies (bo_access/bo_refresh), silent one-shot refresh on 401; LoginForm → username/password → Django; Django `/api/auth/me/` added. E2E verified live | C5,V14,V15 |
| T11 | ✅ | FE: `/sites` page — server-paginated TanStack-free table (view mode card-rows A–I) + inline edit mode (per-role fields) + search + Download XLSX + Tambah Situs Baru (dialog). Verified via BFF live (seeded data: S0104 sync, S0113 manual) | C8,C13,C15 |
| T12 | ✅ | FE: role-based column visibility (visibleColumns mirror of members.rbac) + read-only masking on synced (no Ubah button) | C14,V5 |
| T13 | ✅ | FE: file upload UI (BAA/PO/BAP/invoice) in edit form → BFF multipart proxy → Django upload endpoint (API-verified T6; browser-click flow pending manual QA) | C12 |
| T14 | ✅ | FE: Quota read-only page (Siab GSM/Starlink tabs) | C13 |
| T15 | ✅ | FE: Networks + Organizations read-only pages | C13 |
| T16 | ✅ | FE: deploy config (Dockerfile multi-stage standalone + .dockerignore + env BACKONE_API_URL) | C6 |
| T17 | ✅ | Verified: end-to-end login → list → manual-edit → upload → export; read-only block on synced site; RBAC matrix — API-level live test (servers up) | V5,V12,V13 |
| T18 | . | Post-SPA: relocate Wagtail mount from root `''` to superuser-only `/django-admin/` (swap stock Django admin path); update login/homepage reverse links | C7 |
| T19 | ✅ | Backend: add `Purchasing` to `WRITE_BY_ROLE` (`{"po_file_vendor"}`) + `READ_EXTRA_BY_ROLE` in `members/rbac.py`; add `member_links` to Sales writable set | C20,V23 |
| T20 | ✅ | Backend: relax synced-write gate in `MemberSerializer.update` + `MemberFileSerializer.update` — allow feature fields in role's `writable_fields` on synced, deny CORE/identity on synced (V20). Update `_assert_writable` to drive gate | V5,V20 |
| T22 | ✅ | Backend: dashboard aggregate endpoint per `network_group` — BAA count (`upload_baa!=null`), invoice count (`invoice_number!=null`), dismantle count (`offline_at!=null`); Top Networks retained | C22,V22 |
| T23 | ✅ | FE: `/sites` grid — replace blanket "no Ubah on synced" with role-scoped edit affordance (T12 superseded): Sales edits PO user/link/BAA status, Finance invoice, Purchasing PO vendor; core cols stay read-only | C8,V5,V20 |
| T24 | ✅ | FE: member_links editor — "Add link" per site (create-first; 0/100 prod sites have links), inline edit/delete after creation; fields role/service/provider/capacity/sid | V21,V24 |
| T44 | ✅ | FE: remove `service_line`, `location`, `quota_string` from `scalarDefsFor` in `site-edit-form.tsx`; keep `network` with `displayFor: (r) => r.network_name ?? ""` to show Network Name instead raw PK; add `displayFor` optional field to `ScalarDef` type; coerce `network` to number in submit payload; use `displayFor` for disabled text input display value | V45 |
| T45 | ✅ | FE: add `invoice_number` scalar field for Finance in `scalarDefsFor` (`site-edit-form.tsx`) — field already in Finance `WRITE_BY_ROLE` in `data.ts` (no change needed there) | V45 |
| T46 | ✅ | Backend: updated `members/rbac.py` — narrowed `WRITE_BY_ROLE["Support"]` to `{"ip_address", "member_links"}`; expanded `WRITE_BY_ROLE["Purchasing"]` to `{"po_file_vendor", "project_number"}`; expanded `WRITE_BY_ROLE["Sales"]` to add `{"sdwan_package", "po_file_user"}`; added `project_number` to `READ_EXTRA_BY_ROLE["Purchasing"]` (V46,V47,V48) | V46,V47,V48 |
| T47 | ✅ | FE: updated `WRITE_BY_ROLE` in `data.ts` — Support: `{"ip_address","member_links"}`; Purchasing: `{"po_file_vendor","project_number"}`; Sales: added `{"sdwan_package","po_file_user"}`; `writableFieldSet()` + `isFieldWritable()` automatically reflect changes | V46,V47,V48 |
| T48 | ✅ | Multi-domain sync: add `Networks.domain` (CharField 100, `default=''`) + migration `networks.0004` (AddField + RunPython backfill `''`→`manage.backone.cloud`); `get_networks` keys `_netloc(domain_api)` and scopes the delete list to `filter(domain=domain)`; restore VN cron line in `dockerize/cronjobs`; remove the `backone-data-app` volume mount from `backone-data-crond` (it shadowed `/app` with 2025-10-27 code). Verified: 59 tests OK; `makemigrations --check` no changes; deployed by digest; live VN sync 1207→1228 members / 26→45 networks with bc=26 intact; ping-pong both directions zero deletions; real 11:00 cron tick ran both lines clean | C15,V49,V50 |

| T49 | ✅ | FE: hide Quota/Networks/Pengaturan for `External` + `External Network` — added `nav-access.ts` (`isExternalNavHidden`), `groups` on `NavUserInfo` populated in `(main)/layout.tsx::getCurrentUser()`, `getMeAccess()` in `lib/auth.ts`, `visibleItems(groups)` in `app-sidebar.tsx` (keeps the `settings-lookups` rule, superuser branch first), `redirect("/dashboard/default")` guards in `quota/page.tsx` / `networks/page.tsx` / `organizations/page.tsx`. Verified in-browser: `External` + `External Network` + `External`+`Sales` hybrid → sidebar only Dashboard+Sites, all 3 routes → `/dashboard/default`, `/sites` unaffected; `Sales`-only + superuser → 3 routes 200 and menus intact, superuser keeps `/settings/lookups`; `npm run build` exit 0 | C36,V51 |

| T25 | ✅ | FE: file upload UI for feature files on synced sites (PO user / PO vendor / invoice) → BFF multipart → Django upload; size/ext errors surface (10MB, PDF/XLS/XLSX/DOC/DOCX) | C23,T13,V20 |

| T38 | ✅ | Backend: migration — add DB `unique=True` on `SdwanPackage.name`/`BaaStatus.name`/`LinkRole.name` (V38); `LookupViewSet`(s) — `/api/lookups/{kind}/` list+create, `<id>/` PATCH rename, custom `IsSuperUser` permission (`is_superuser`) on all methods (**not** `IsAdminUser`); serializer `{id, name}`; view built from mixins excluding destroy (no DELETE route, V39); `kind` → `SdwanPackage`/`BaaStatus`/`LinkRole` | C28,C29,C32,V37,V38,V39,V43,V44 |
| T39 | ✅ | FE: `/settings/lookups` page + sidebar item gated on `me.is_superuser` — **plumb `is_superuser` into the nav chain** (`getCurrentUser()` in main layout → `NavUserInfo` → sidebar), filter the `/settings/lookups` item out unless `is_superuser`; 3 sections (SDWAN/BAA/Role) from one reusable component parameterized by `kind`; config-only, no assignment UI; add + rename flows to the DRF endpoints | C28,C30,C31,C32,V37,V41 |
| T40 | ✅ | FE: route guard — `/settings/lookups` redirects non-superusers to `/dashboard/default`; superuser only. Backend rejects any direct non-superuser API call (custom permission, 403) (V37) | C28,V37,V43 |
| T41 | ✅ | Verified: superuser sees `/settings/lookups` + can add/rename in all 3 sections; non-superuser gets no nav entry, route redirect, and 403 on direct API call; duplicate name → inline 400; `/sites` selects still work from `/api/members/options/` (V40); 27 backend tests + `manage.py check` pass | V37,V38,V39,V40,V41,V43,V44 |
| T42 | x | Backend: make `member_code` (Kode Situs) a Sales-writable feature field — remove `member_code` from `CORE_EDIT_FIELDS` (rbac.py:20), add to `FEATURE_FIELDS` (rbac.py:1) + `WRITE_BY_ROLE["Sales"]` (rbac.py:34); drop `member.member_code = member_code` from sync (`members/utils.py:47`, and the now-unused `member_code = resp_json[...]` at :28) so sync never clobbers Sales' code. Keep `member_code` in `CORE_FIELDS` (rbac.py:51) — stays readable/exported/searchable grid-wide. Verified: 35 members tests OK (incl. new V6 sync-never-clobbers + V5 Finance-denied/Sales-writes tests), 47 full-suite OK, `manage.py check` clean | C8,C11,V5,V6,V20 |
| T43 | x | FE: add `member_code` to the Sales edit branch (`site-edit-form.tsx:48`) so Sales can set/change Kode Situs on manual + synced sites; Support branch already has it. No read/grid change (Kode Situs stays in the always-visible `situs` column). Verified: `npm run build` clean | C8,V5 |
| T27 | ✅ | Backend: fix role queryset (`member_queryset_for`) so dismantled (`offline_at<=now`) sites stay READ+summarizable Sales/Finance/Purchasing — separate active-sites filter aggregate/detail visibility; per-group dismantle count over full role set, not active queryset; add dismantle filter param sites list | C22,V22,V25 |

| T28 | x | FE: `/sites` table — fit columns to viewport (compress/truncate per-cell, no `overflow-x-auto` horizontal scroll; keep all columns), Action/"Ubah" always visible at typical desktop width | C13,V26 |
| T29 | x | FE: remove global header search — drop `<SearchDialog />` from `(main)/layout.tsx` header + import; delete obsolete `search-dialog.tsx` + `components/ui/command.tsx` (used only by it); header = sidebar toggle + page title | V27 |
| T30 | x | FE: remove sidebar Quick Create + Inbox row — delete the `SidebarGroup` block (Quick Create primary button + Inbox button) from `nav-main.tsx`; drop now-unused `MailIcon`/`PlusCircleIcon` imports; sidebar opens directly at nav groups | V28 |
| T32 | x | FE: login left panel (desktop) — replace `bg-primary` with a random `picsum.photos` background image (random seed per load) + translucent scrim so logo/title stay legible; panel stays `hidden lg:block lg:w-1/3` | V30 |
| T31 | x | FE: copy `backone-logo.svg` to FE `public/` (done) + render as brand mark in sidebar header (`app-sidebar.tsx`) + login left panel (`(auth)/auth/v1/login/page.tsx`), replacing `Globe` icons; set `metadata.icons` to use it as favicon (root `layout.tsx`); keep brand text | V29 |
| T33 | x | Backend: new snippet models `SdwanPackage`, `BaaStatus`, `LinkRole` in `members/models.py` (mirror `Links`: `name` CharField, timestamps, `verbose_name`); register as Wagtail snippets with `user_can_delete_obj=False` in `members/wagtail_hooks.py` (links `LinksViewSet` template) | C24,V33 |
| T34 | x | Backend: migration `members.0012` — create 3 tables, seed rows (C26), backfill existing `CharField` values→FK rows (prod has only `BackOne - SDWAN Pro`, `New Link`, `BACKUP`), then convert `Members.sdwan_package`/`baa_status_category` + `MemberLink.role` CharField→FK. Data-safe, no loss/orphan (C27,V34) | C26,C27,V34 |
| T35 | x | Backend: serialize — `sdwan_package`/`baa_status_category`/`role` become `SlugRelatedField(slug_field="name")` (resolves the **string name** the FE sends → FK row on write; FK name via `to_representation` on read); drop `ChoiceField` + `SDWAN_PACKAGE_CHOICES`/`BAA_STATUS_CHOICES`/`LINK_ROLE_CHOICES`. Update the sites **list** (DRF serializer output) + **export** rows (`apis.py` export + the list read-builder in `apis.py`) to emit the lookup `name` string, not the FK instance. Also make `MemberLink.__str__` emit `self.role.name` | C25,V32,V35,V36 |
| T36 | x | Backend: new `MemberOptionsViewSet` action (or `@action`) at `/api/members/options/` returning the three option lists from the tables (sdwan/baa/role as string arrays) — feeds FE selects | C25,V31 |
| T37 | x | FE: drop hard-coded `SDWAN_CHOICES`/`BAA_STATUS_CHOICES` from `data.ts` + `["MAIN","BACKUP","SINGLE"]` from `site-edit-form.tsx` + `SDWAN_CHOICES` use in `create-site-dialog.tsx` (L21/L115); fetch the option lists from `/api/members/options/` and use them for the sdwan/baa/role selects | C25,V31 |
| T50 | ✅ | Backend: harden Axes lockout — hoist `from datetime import timedelta` to module imports (it was bound *after* the AXES block, so using it there would `NameError`) and drop the old duplicate at the `SIMPLE_JWT` block; `AXES_COOLOFF_TIME = timedelta(minutes=float(os.getenv('AXES_COOLOFF_TIME', 30)))` (explicit unit, 30m default); `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False`; `env.sample` states the unit; regression test `accounts/tests.py::AxesLockoutTest` (explicit unit / retry-while-locked does not extend / lockout expires unattended). Verified: 2 of 3 tests FAIL pre-fix, 66 full-suite OK | C37,V52 |

## §B — Bugs

| ID | Date | Cause | Fix |
|---|---|---|---|
| B1 | 2026-09-08 | API endpoint `get_members_by_user` had no auth check | Added `@login_required` (`members/views.py:60`) |
| B2 | 2026-09-08 | `get_quota_usage()` NameError on empty quota_string | Init `quota_usage = 0` before block |
| B3 | 2026-09-08 | Sync deleted all networks on failed upstream call | Early return on API failure; only populate list after success |
| B4 | 2026-09-09 | Both write serializers (`MemberSerializer.update`, `MemberFileSerializer.update`) hard-blocked ALL `is_manual=False` (synced) writes — would reject Sales/Finance/Purchasing feature edits on the 1,534 prod synced sites | Amend gate to feature-field-permissive on synced (V5/V20); core/identity stay read-only |
| B5 | 2026-09-17 | `get_networks()` seeded its delete list from ALL `Networks` rows with no domain filter, so a second upstream's sync treated every other domain's network ids as deleted and removed them, CASCADE-deleting their Members — enabling the vn cron line would have destroyed all 1207 backone sites | Add `Networks.domain` + migration `networks.0004` (backfills existing 26 rows to `manage.backone.cloud`); scope `current_networks_list` to `filter(domain=domain)`. Cite V49 |
| B6 | 2026-09-17 | Prod user `mzainuri@backone.cloud` could not log in. `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT` defaulted `True`, so every attempt made while locked — even one with the CORRECT password — rewrote `attempt_time` and restarted the full cool-off: a user who retried never healed and the lockout looked permanent. Compounded by `AXES_COOLOFF_TIME = 2` being read by django-axes as 2 **HOURS**, not minutes. Both surfaced as a wrong-password 401 (SimpleJWT emits the same `no_active_account` message for a locked account, so the cause was invisible) | Set `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False` plus an explicit `timedelta(minutes=...)` default 30 (V52/C37); prod service env `AXES_COOLOFF_TIME=2` → `30`. Cite V52 |
