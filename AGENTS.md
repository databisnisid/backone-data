# Repository Guidelines

## Project Overview

**BackOne Data** is an internal ISP network management and site monitoring dashboard for Indonesian network operator BackOne. Built on Django 4.2 + Wagtail 5.2 CMS (admin-only, no Wagtail pages/documents). Tracks deployment sites (members), network groupings, bandwidth quota monitoring (DPI/Starlink), BAA document uploads, invoice tracking, and a Google Maps-based geospatial dashboard with online/offline status visualization. Data syncs hourly from upstream API (`manage.backone.cloud`).

Production URL: `https://manage.backone.cloud`

## Architecture & Data Flow

**Pattern:** Monolithic Django MVT. Wagtail used purely as admin panel via `ModelAdmin` (replaces Django admin). Thin JSON API layer serves the frontend map dashboard.

```
Upstream API (manage.backone.cloud)
  → hourly cron (config/workers.py sync_data)
    → networks/utils.py (get_networks) — upsert Networks/NetworksGroup
    → members/utils.py (get_members_all) — upsert Members by member_id
  → MySQL/SQLite via Django ORM
  → Wagtail admin UI (CRUD + RBAC by Django Groups)
  → JSON API: /api/members/get_by_user/<id>/
    → Google Maps JS dashboard (map_dashboard.js)
    → Marker rendering with WKT POINT geometry
```

## Key Directories

| Directory | Purpose |
|---|---|
| `config/` | Django project settings, URL routing, WSGI/ASGI, gunicorn configs, cron workers |
| `accounts/` | Custom User model (`AUTH_USER_MODEL = 'accounts.User'`), Organizations, custom Wagtail user forms |
| `members/` | **Core domain** — Members/Sites model (`ClusterableModel`), geo views, JSON API, data sync utils |
| `networks/` | Networks + NetworksGroup models, sync utils (upstream API upsert/delete) |
| `links/` | Simple Links model (service types) attached to Members via M2M |
| `quota/` | Proxy models: `MembersDpi`, `MembersStarlink` — filter Members by `quota_string` content |
| `dashboard/` | Homepage panels (MapSummaryPanel, NetworksPanelSummary), Wagtail hooks, Google Maps JS/CSS, SVG logos |
| `templates/` | Overridden Wagtail admin templates (login, home, base, axes lockout) |
| `dockerize/` | Dockerfiles, cron configuration, Docker env |

## Development Commands

```bash
# Local dev
pip install -r requirements.txt
cp env.sample .env          # configure env vars
python manage.py migrate
python manage.py runserver 0.0.0.0:8009

# Production start
gunicorn -c config/gunicorn.py   # port 8009

# Docker dev
./entrypoint.ds                 # collectstatic → migrate → runserver :8008

# Docker prod
./entrypoint_gunicorn.ds        # collectstatic → migrate → gunicorn :8008

# Cron (hourly data sync)
./dockerize/cronjobs            # calls config.workers.sync_data()

# Tests (currently empty stubs — zero test coverage)
python manage.py test
python manage.py test members
```

## Code Conventions & Common Patterns

### Naming
- **snake_case** everywhere; apps lowercase singular (`members`, `networks`, `links`)
- Models PascalCase; utility functions snake_case
- Wagtail ModelAdmin classes suffixed `Admin` / `AdminGroup` (e.g. `MembersAdmin`, `NetworksAdminGroup`)
- Files: `wagtail_hooks.py` for admin registration, `utils.py` for sync/data logic

### Key Patterns
- **Proxy models** for filtered views (`MembersDpi` / `MembersStarlink` subclass `Members` with custom managers)
- **`ClusterableModel`** for inline M2M editing in Wagtail admin
- **`crum.get_current_user()`** for request user access outside views
- **Group-based RBAC** via Django Groups: Sales, Finance, Support, External
- **Panel composition** in Wagtail homepage via custom Wagtail Components (`MapSummaryPanel`, `NetworksPanelSummary`)
- **Upsert by exception**: try `get`, catch `ObjectDoesNotExist`, then `create` — no `get_or_create` in sync utils

### Error Handling
- `try/except ObjectDoesNotExist` for upsert in sync utils
- `try/except KeyError` in panel building
- `requests.exceptions.HTTPError` catching with `print()` logging
- No custom exception classes or structured error responses

### Types & Async
- Minimal type hints — only on some model methods (return `str`)
- **All synchronous** Django function-based views; no async Python
- Frontend: `map_dashboard.js` uses `async/await` `fetch()` — only async code in project

### i18n
- Indonesian locale (`id-id`), `Asia/Jakarta` timezone
- `gettext_lazy` for all model `verbose_name`/`verbose_name_plural`

## Important Files

| File | Role |
|---|---|
| `manage.py` | Django management CLI (`DJANGO_SETTINGS_MODULE=config.settings`) |
| `config/settings.py` | All Django settings (DB, middleware, installed apps, Wagtail config) |
| `config/urls.py` | URL routing: `/django-admin/`, `/api/members/`, Wagtail admin at root |
| `config/workers.py` | `sync_data()` — hourly cron entrypoint, orchestrates network + member sync |
| `config/gunicorn.py` | Local gunicorn config (5 sync workers, port 8009) |
| `config/gunicorn_docker.py` | Docker gunicorn config (port 8008) |
| `members/models.py` | Core `Members(ClusterableModel)` — 274 lines, geo, quota, BAA, invoice |
| `members/views.py` | JSON API: `get_members_by_user()`, `prepare_data()` (WKT POINT parsing) |
| `members/utils.py` | `get_members_all()` — upstream API fetch + ORM upsert |
| `networks/utils.py` | `get_networks()` — upstream API fetch + upsert/delete |
| `accounts/models.py` | Custom `User(AbstractUser)` with organization FK |
| `dockerize/Dockerfile` | Python 3.11-alpine, MariaDB dev, Asia/Jakarta TZ |
| `dockerize/Dockerfile.bvn` | Python 3.10-alpine variant with Node.js |
| `env.sample` | Local dev env template (SQLite, MQTT, SSH, Google Maps, Redis, Axes) |
| `requirements.txt` | Pinned dependencies (pip, no poetry/pip-tools) |

## Runtime & Tooling Preferences

- **Runtime:** Python 3.10–3.11 (per Dockerfiles)
- **Package manager:** pip with `requirements.txt` — no poetry, pip-tools, or pyproject.toml
- **Web server:** Gunicorn 21.2.0 (sync workers)
- **Database:** SQLite3 (dev default), MySQL/MariaDB (production)
- **Cache:** Redis (configured in env.sample)
- **No linting, formatting, or type checking** configured — no flake8, ruff, mypy, black, isort
- **No CI/CD pipeline** — no GitHub Actions, GitLab CI, or Jenkins
- **No pre-commit hooks** or git hooks of any kind
- **Timezone:** `Asia/Jakarta` (W-7)
- **Key integrations:** MQTT (IoT presence/rcall topics), Google Maps API, SSH, Google reCAPTCHA

## Testing & QA

**Status: Zero automated test coverage.** All 6 app `tests.py` files are empty Django scaffolding stubs.

```bash
python manage.py test          # runs 0 tests
python manage.py test members  # per-app (still 0 tests)
```

- **Framework:** Django built-in (`django.test.TestCase` wrapping `unittest`) — no pytest
- **Test structure:** Co-located `tests.py` per app (Django convention), no `tests/` subdirectories
- **No fixtures, factories, mocks, conftest, or shared test base classes**
- **Coverage:** No `.coveragerc` or coverage config; `.gitignore` lists `.coverage` / `htmlcov/` (awareness, not implementation)
- **Manual coverage:** `coverage run manage.py test && coverage report`

### Key Integrations for Testing

- **Upstream API** (`manage.backone.cloud`) — sync utils make HTTP calls; needs mocking for unit tests
- **MQTT** — presence tracking; needs broker mock
- **Google Maps** — frontend-only; no server-side dependency
- **SSH** — credentials in env; likely needs mocking
