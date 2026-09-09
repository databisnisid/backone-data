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
| C8 | **Sync-as-authority (amended)**: sites fed by upstream cron are **read-only for CORE/identity fields** (C11); **user-owned feature fields ARE writable** by authorized roles on synced sites — PO user, PO vendor, invoice number+file, BAA status, `member_links` (provider/service/sid/capacity), notes. Identity/network/timeline stay immutable. Only manual sites get full core-field edits |
| C9 | Manual sites marked `Members.is_manual=True`. Distinguish manual vs synced by this flag (not by absent upstream id) |
| C10 | IP address field editable ONLY on manual sites (Support role writes it) |
| C11 | Upstream payload fields sync owns (read-only): name, address, location(WKT), online_at, offline_at, network, service_line, quota_string, member_code. Everything else is user-owned |
| C12 | Uploads (BAA download for sync sites / upload for Finance-Sales / PO user / PO vendor / bukti invoice / BAP) stored in Django MEDIA, served/proxied via BFF |
| C13 | Row scale: **server-paginated** (100/page), server filter + sort + total count, server-side XLSX export. No client virtualization/AG Grid |
| C14 | RBAC retains Django Groups (Sales, Finance, Purchasing, Support, External/External Network) + org-filtering; enforced server-side in DRF, mirrored as column visibility in FE |
| C15 | Sync untouched for now (data-source authority): `config/workers.sync_data` + `dockerize/cronjobs` hourly unchanged |
| C16 | SQLite dev / MySQL prod (existing) |
| C17 | `id-id` locale, `Asia/Jakarta` TZ |
| C18 | No CI/CD, no linter/typecheck config added (repo convention) |
| C19 | `SECRET_KEY` read from env (`os.getenv('SECRET_KEY')`, dev fallback only); JWT signed with this key — production MUST set real `SECRET_KEY` before `/api/sites/` protected endpoints deploy |

| C20 | **Purchasing** Django Group added (prod id=11, created) — writable ONLY `po_file_vendor`. Not in org-filter (`_is_authorized_all` unchanged: Support/External inherit all rows) |
| C21 | **Dismantle = derived view** of `Members.offline_at != null` — no new column/status, no migration, no drift (Q3/Q7) |
| C22 | Dashboard aggregates ship **per `network_group`** (NetworksGroup): BAA = `upload_baa` non-null; Invoice = `invoice_number` non-null (Q7). Top Networks retained, dismantle count folds into Online/Offline cards |
| C23 | **File upload cap 10MB / PDF,XLS,XLSX,DOC,DOCX** (existing `MAX_UPLOAD_SIZE`+`ALLOWED_UPLOAD_EXT`, already enforced in `MemberFileSerializer`) — reused, not re-added |
## §R — Research

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
| Django | `/api/quota/` | DRF ViewSet | Read-only Quota lists |
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
| B SDWAN pkg | **`sdwan_package`** CharField choices: `BackOne - SDWAN Lite|SDWAN Pro|SDWAN Gateway|Tanpa SDWAN` | editable manual |
| B Project no. | **`project_number`** | editable manual |
| B Networks | `network` FK (auto) | read-only |
| B multi-link | **new child `MemberLink`** (ParentalKey→Members via ClusterableModel): `label`(MAIN/BACKUP/SINGLE), `service_type` FK→Links?, `provider` CharField, `capacity` CharField, `sid` CharField | editable manual; links on synced read-only |
| C Timeline | `online_at`, `offline_at` (exist) | read-only on sync |
| D Status BAA | **`baa_status_category`** choices: New Link\|Upgrade Link\|Downgrade Link\|Relokasi | editable manual; on synced only Support/…masked |
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
| Support | all (unmasked cols) | manual full + synced core/timeline | BAA/PO/BAP | yes | creates manual sites |
| Sales | org | synced: `po_file_user`, `member_links`, `baa_status_category`, notes | PO user | yes | write-on-synced (C8) |
| Purchasing | org | synced: `po_file_vendor` | PO vendor | yes | new group (C20) |
| Finance | org | synced: `invoice_number`, `invoice_file`, notes | invoice file | yes | isolated |
| External / External Network | org (already visible) | no | BAA download | no | read-only map + sites |

### Cron

Unchanged: `0 * * * * python /app/manage.py shell --command "from config.workers import sync_data; sync_data('https://manage.backone.cloud')"` (`dockerize/cronjobs`).

## §V — Invariants

| ID | Invariant |
|---|---|
| V1 | `Members.member_id` unique; sync upserts by it (existing) |
| V2 | `Networks.network_id` unique; sync upserts by it (existing) |
| V3 | Sync never deletes Members — upsert only (existing) |
| V4 | `Members.is_manual=True` ⟺ site created via "Tambah Situs Baru"; synced sites `is_manual=False` |
| V5 | **Write-scope rule (amended)**: CORE/identity fields immutable on synced sites (`is_manual=False`) — update/delete/upload of those blocked server-side. **Feature/user-owned fields ARE writable on synced** by authorized roles (C8): `po_file_user`, `po_file_vendor`, `invoice_number`, `invoice_file`, `baa_status_category`, `member_links`, notes. FE shows view mode for core, edit mode for permitted feature fields |
| V6 | Sync writes only C11-whitelisted fields; never writes `is_manual`, `ip_address`, `sdwan_package`, `project_number`, `po_file_*`, `bap_file`, `invoice_file`, `baa_status_category`, notes |
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
| V20 | **Synced-site write gate**: `MemberSerializer.update()` + `MemberFileSerializer.update()` relax the `is_manual` guard to check each proposed field — allow feature field if in role's `writable_fields`, deny CORE/identity fields on synced. No blanket synced-write (V5) |
| V21 | **MemberLink write on synced**: `member_links` create+update permitted for Sales on synced sites (C8). Links are user-owned (never in C11 sync-whitelist), thus immune to upstream overwrite |
| V22 | **Dismantle derived**: dismantle set = `Members.offline_at IS NOT NULL`. No `status`/`dismantle_at` column. Count = filter, not stored |
| V23 | **Purchasing RBAC**: `WRITE_BY_ROLE["Purchasing"] = {"po_file_vendor"}` + `READ_EXTRA_BY_ROLE` includes it. Org-filtered like Sales/Finance (`_is_authorized_all` unchanged — not in the Support/External all-rows set) |
| V24 | **Nested MemberLink write path**: `member_links` is a writable nested serializer, not `read_only=True`; create/update/delete of links flows through DRF + `save_child_instances` on `Members.save()` — never a raw modelcluster bypass that skips a role/field check. Sales may write links on synced + manual; other roles link read-only |
| V25 | **Dismantled-site visibility**: `offline_at <= now` (dismantled) sites remain READ + summarizable for role-filtered users (Sales/Finance/Purchasing) — allows PO/invoice fill on dismantled sites and correct per-group dismantle counts. Only the default "active sites" list filters them out; aggregates + detail must not double-filter (BLOCK-2 fix) |

## §T — Tasks

| ID | Status | Task | Cites |
|---|---|---|---|
| T1 | ✅ | Backend: deps `djangorestframework-simplejwt==5.5.1` + `drf-spectacular==0.30.0` in requirements.txt; wire SimpleJWT auth + Swagger/OpenAPI (`/api/schema/`, `/api/docs/`) | C3 |
| T2 | ✅ | Backend: migrate `Members` + new fields; new `MemberLink` model; `is_manual` default False; nullable network guard | V4,V6,V8 |
| T3 | ✅ | Backend: DRF auth wiring (SimpleJWT login/refresh endpoints, `IsAuthenticated`) | C3,V11 |
| T4 | ✅ | Backend: `SitesViewSet` list (server pagination + filter + sort + total count), detail (read-only auto), update manual-only | V5, C13 |
| T5 | ✅ | Backend: RBAC permission class (Sales/Finance/Support/External org filtering + field-level write gate) | C14,V12 |
| T6 | ✅ | Backend: file upload/serve endpoint (BAA/PO user/vendor/invoice/BAP), MEDIA storage, validation, delete cascade on member delete | C12,V9,V10 |
| T7 | ✅ | Backend: XLSX export endpoint honoring RBAC | C13,V13 |
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
| T21 | ✅ | Backend: **new nested MemberLink write** — replace `member_links=MemberLinkSerializer(many=True, read_only=True)` with writable nested serializer; add `MemberLinkViewSet`(s) or nested action under `SitesViewSet` for create/update/delete of links on synced+manual; Sales-only per V23; ParentalKey children saved via `save_child_instances` (ClusterableModel), never raw `.save()` bypassing RBAC | V21,V24 |
| T22 | ✅ | Backend: dashboard aggregate endpoint per `network_group` — BAA count (`upload_baa!=null`), invoice count (`invoice_number!=null`), dismantle count (`offline_at!=null`); Top Networks retained | C22,V22 |
| T23 | . | FE: `/sites` grid — replace blanket "no Ubah on synced" with role-scoped edit affordance (T12 superseded): Sales edits PO user/link/BAA status, Finance invoice, Purchasing PO vendor; core cols stay read-only | C8,V5,V20 |
| T24 | . | FE: member_links editor — "Add link" per site (create-first; 0/100 prod sites have links), inline edit/delete after creation; fields role/service/provider/capacity/sid | V21 |

| T25 | . | FE: file upload UI for feature files on synced sites (PO user / PO vendor / invoice) → BFF multipart → Django upload; size/ext errors surface (10MB, PDF/XLS/XLSX/DOC/DOCX) | C23,T13 |
| T26 | . | FE: dashboard — group cards for BAA per group + Invoice per group (network_group), dismantle count folded into Online/Offline; keep Top Networks | C22,V22
| T27 | ✅ | Backend: fix role queryset (`member_queryset_for`) so dismantled (`offline_at<=now`) sites stay READ+summarizable Sales/Finance/Purchasing — separate active-sites filter aggregate/detail visibility; per-group dismantle count over full role set, not active queryset; add dismantle filter param sites list | C22,V22,V25 |

## §B — Bugs

| ID | Date | Cause | Fix |
|---|---|---|---|
| B1 | 2026-09-08 | API endpoint `get_members_by_user` had no auth check | Added `@login_required` (`members/views.py:60`) |
| B2 | 2026-09-08 | `get_quota_usage()` NameError on empty quota_string | Init `quota_usage = 0` before block |
| B3 | 2026-09-08 | Sync deleted all networks on failed upstream call | Early return on API failure; only populate list after success |
| B4 | 2026-09-09 | Both write serializers (`MemberSerializer.update`, `MemberFileSerializer.update`) hard-blocked ALL `is_manual=False` (synced) writes — would reject Sales/Finance/Purchasing feature edits on the 1,534 prod synced sites | Amend gate to feature-field-permissive on synced (V5/V20); core/identity stay read-only |
