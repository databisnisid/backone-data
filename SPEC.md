# SPEC.md — BackOne Data

## §G — Goal

ISP network management dashboard for BackOne. Tracks deployment sites (members),
networks, quota (DPI/Starlink), BAA docs, invoices. Google Maps geospatial view.
Hourly sync from upstream API (`manage.backone.cloud`). Wagtail admin for CRUD.

## §C — Constraints

| ID | Constraint |
|---|---|
| C1 | Django 5.2.17 LTS + Wagtail 7.4 LTS (admin-only, no CMS pages) |
| C2 | Python 3.10–3.14 (Dockerfiles + dev) |
| C3 | SQLite3 dev, MySQL/MariaDB prod (`requirements.txt` pins `mysqlclient==2.1.1`) |
| C4 | `pip` + `requirements.txt` (no poetry/pip-tools/pyproject.toml) |
| C5 | Gunicorn 21.2.0 sync workers (5 workers) |
| C6 | No linter, formatter, type checker, or CI/CD configured |
| C7 | 39 automated tests across 5 test files (`members`, `networks`, `quota`, `dashboard`) |
| C8 | `id-id` locale, `Asia/Jakarta` timezone |
| C9 | `AUTH_USER_MODEL = 'accounts.User'` (custom, with org FK) |
| C10 | 20+ env vars via `python-dotenv` (`env.sample`) |
| C11 | Docker deployment: Alpine Python 3.13, crond for hourly sync |
| C12 | Brute-force protection via django-axes ≥7.1.0 (Django 5.2 compatible) |
| C13 | `wagtailgeowidget` 9.1.0 for Google Maps geo fields |
| C14 | Redis configured in env but not wired in settings.py ? |
| C15 | `wagtail.contrib.modeladmin` → `wagtail_modeladmin` (5 wagtail_hooks.py files) |
| C16 | Bump all pinned deps in requirements.txt to latest (not just Django/Wagtail) |

## §I — Interfaces

### URL Routes (`config/urls.py`)

| Route | Target | Purpose |
|---|---|---|
| `/django-admin/` | Django admin | Standard Django admin (minimal use) |
| `/api/members/get_by_user/<int:user>/` | `members.views.get_members_by_user` | JSON API — map dashboard data |
| `''` (root) | Wagtail admin URLs | Primary admin UI |

### Models

| App | Model | Table | Key Fields |
|---|---|---|---|
| `accounts` | `User(AbstractUser)` | `auth_user` | `organization` FK → `Organizations` |
| `accounts` | `Organizations` | `organizations` | `name`, `networks` M2M → `Networks`, `is_no_org` |
| `networks` | `NetworksGroup` | `networks_group` | `name` |
| `networks` | `Networks` | `networks` | `name`, `network_id` (unique), `network_group` FK |
| `members` | `Members(ClusterableModel)` | `members` | `member_id` (unique), `network` FK, `links` M2M, `location` (WKT), `quota_string`, `upload_baa`, `online_at`/`offline_at` |
| `links` | `Links` | `links` | `name` |
| `quota` | `MembersDpi` | proxy of `Members` | Custom manager: `quota_string__contains='dpi'` |
| `quota` | `MembersStarlink` | proxy of `Members` | Custom manager: `quota_string__contains='starlink'` |

### Wagtail ModelAdmin Panels

| Panel | Menu | Model | RBAC |
|---|---|---|---|
| `MembersAdmin` | Sites | `Members` | Org-filtered; create disabled; delete: superuser only |
| `NetworksAdmin` | Networks | `Networks` | ? |
| `OrganizationsAdmin` | Settings | `Organizations` | Delete: cannot delete id=1 |
| `QuotaDpiAdmin` | Quota > Siab GSM | `MembersDpi` | Read-only; org-filtered |
| `QuotaStarlinkAdmin` | Quota > Starlink | `MembersStarlink` | Read-only; org-filtered |

### External Integrations

| Service | Purpose | Config |
|---|---|---|
| Upstream API (`manage.backone.cloud`) | Data sync (networks + members) | `domain_api` passed to `sync_data()` |
| MQTT | IoT presence/rcall topics | `MQTT_USER/PASS/HOST/PORT/TOPIC_*` |
| Google Maps | Geospatial dashboard | `GOOGLE_MAPS_V3_APIKEY` |
| SSH | Remote device access ? | `SSH_DEFAULT_USER/PASS` |
| Redis | Cache ? | `REDIS_URL` (configured in env, not wired in settings) |

### Cron

| Schedule | Command | Purpose |
|---|---|---|
| Hourly | `manage.py shell < dockerize/cronjobs` | `sync_data(domain_api)` — networks + members sync |

## §V — Invariants

| ID | Invariant | Source |
|---|---|---|
| V1 | `Members.member_id` is unique; sync upserts by this field | `members/models.py:18`, `members/utils.py:58` |
| V2 | `Networks.network_id` is unique; sync upserts by this field | `networks/models.py:23`, `networks/utils.py:29` |
| V3 | Sync deletes Networks not present in upstream API response | `networks/utils.py:46-48` |
| V4 | Members are never deleted by sync (upsert only) | `members/utils.py` — no `.delete()` call |
| V5 | Online status: `is_online=1` if `offline_at is None` OR `offline_at >= now()` | `members/views.py:48-51` |
| V6 | `quota_string` parsed as `/-`-delimited: `[0]=current`, `[1]=total`, `[2]=day`, `[3]=type` | `members/models.py:89-192` |
| V7 | Map API filters: org users see only their org's online members; superusers see all | `members/views.py:60-67` |
| V8 | Dashboard panels filter by org; External group gets different template | `dashboard/summary_panels.py:39-56` |
| V9 | Members cannot be created via admin UI (`user_can_create = False`) | `members/wagtail_hooks.py:32-33` |
| V10 | ` Members.delete()` also deletes associated `upload_baa` file | `members/models.py:77-80` |
| V11 | Proxy models `MembersDpi`/`MembersStarlink` filter by `quota_string` contains | `quota/models.py:6-13` |
| V12 | Sync iterates all Networks, fetches members per network from upstream | `members/utils.py:81-86` |
| V13 | Coordinate overlap: markers with same lat/lng get randomized offset | `members/views.py:11-18` |
| V14 | `location` stored as WKT string (`POINT(lng lat)`); parsed on read | `members/views.py:27-30` |
| V15 | API endpoint requires authenticated session (`@login_required`) | `members/views.py:60` |
| V16 | Sync network deletion only runs if API response is valid non-empty list | `networks/utils.py:16-18` |
| V17 | `get_quota_usage()` returns "0GB" when `quota_string` is empty | `members/models.py:122` |
| V18 | WKT parse failure (`AttributeError`/`IndexError`) falls back to default location | `members/views.py:31-33` |
| V19 | Coordinate dedup is O(n²); acceptable at current scale (~hundreds members) | `members/views.py:11-18` |
| V20 | Dashboard panels require authenticated user; anonymous access undefined behavior | `dashboard/summary_panels.py:35-36` |
| V21 | `except (IndexError, ValueError)` — all quota methods use correct tuple syntax | `members/models.py:98,114,152,170,177,184` |
| V22 | Brute-force lockout behavior unchanged after axes upgrade: login failures tracked, cooloff enforced | config/settings.py:203-207 |

## §T — Tasks

| ID | Status | Task | Cites |
|---|---|---|---|
| T1 | x | Add tests for `Members` model quota parsing methods | V6 |
| T2 | x | Add tests for `prepare_data()` WKT parsing edge cases (None, malformed) | V14,V13 |
| T3 | x | Add tests for `get_members_by_user()` org filtering logic | V7,V15 |
| T4 | x | Add tests for `get_networks()` upsert + delete logic | V2,V3,V16 |
| T5 | x | Add tests for `get_members_by_net()` upsert logic | V1,V4 |
| T6 | x | Add tests for online/offline status determination | V5 |
| T7 | x | Add tests for `MembersDpi`/`MembersStarlink` proxy model filtering | V11 |
| T8 | x | Add tests for `NetworksPanelSummary` panel context computation | V8 |
| T9 | x | Wire Redis cache in settings.py if intended (currently env config only) | C14 |
| T10 | ✅ | Fix: `get_quota_usage()` returns "0GB" when `quota_string` empty | V6,V17 |
| T11 | x | Add logging to sync utils instead of `print()` statements | V12 |
| T12 | ✅ | Fix: `except IndexError or ValueError` → `except (IndexError, ValueError)` | V6,V21 |
| T13 | ✅ | Fix: add `@login_required` to `get_members_by_user` API view | V15 |
| T14 | ✅ | Fix: guard sync network deletion on API response validity | V16 |
| T15 | x | Bump Django 5.2 LTS + Wagtail 7.4 LTS + axes ≥7.1.0 + all deps; migrate modeladmin imports | C1,C12,C15,C16 |
## §B — Bugs

| ID | Date | Cause | Fix |
|---|---|---|---|
| B1 | 2026-09-08 | API endpoint `get_members_by_user` had no auth check — anonymous users could fetch member data | Added `@login_required` decorator (`members/views.py:60`) |
| B2 | 2026-09-08 | `get_quota_usage()` raised `NameError` when `quota_string` empty — `quota_usage` unbound | Initialized `quota_usage = 0` before conditional block (`members/models.py:122`) |
| B3 | 2026-09-08 | Sync deleted all networks if upstream API call failed — `response_json` stayed `[]`, `current_networks_list` full | Early return on API failure; only populate `current_networks_list` after successful response (`networks/utils.py:16-18`) |
