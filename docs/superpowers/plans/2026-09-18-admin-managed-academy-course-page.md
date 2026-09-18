# Admin-Managed Academy Course Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an authenticated Django Academy course catalogue and detail player whose published content is managed in Django admin, fetched through `/api/v1/`, and supports validated YouTube embeds.

**Architecture:** Add a focused `apps.academy` domain with learning paths, courses, and ordered typed modules. Django admin owns content authoring; read-only DRF endpoints serve only published content; the preserved Academy CSS powers a Django page whose JavaScript fetches and renders API data. Store administrator-provided YouTube URLs, validate supported hosts, derive the video ID, and construct a safe embed URL with the current request origin instead of storing iframe HTML.

**Tech Stack:** Django 6.0.4, Django REST Framework 3.17.1, SQLite development migrations, Django admin, vanilla JavaScript, existing SME Academy CSS.

**Spec:** `Master Plan.md` sections 4, 6, 8, 14–19

**Execution status:** Implemented and automatically verified on 18 September 2026. The in-app browser connection was unavailable, so the visual browser journey remains a manual smoke-test item; authenticated Django view/API coverage passed.

## Global Constraints

- Work in the current workspace as explicitly approved; preserve unrelated edits.
- Follow red-green-refactor for every production behavior.
- Do not restyle existing CRM applications.
- New frontend requests use `/api/v1/` only.
- Do not store or render arbitrary administrator-provided iframe HTML.
- Only published paths, courses, and modules appear to ordinary users.
- Do not load the prototype `academy/js/data.js` from the Django page.
- Marketing remains out of scope.

---

### Task 1: Academy content model and YouTube validation

**Files:**
- Create: `apps/academy/__init__.py`
- Create: `apps/academy/apps.py`
- Create: `apps/academy/models.py`
- Create: `apps/academy/validators.py`
- Create: `apps/academy/tests/__init__.py`
- Create: `apps/academy/tests/test_models.py`
- Create: `apps/academy/migrations/0001_initial.py`
- Modify: `jbs_crm/settings/base.py`

**Interfaces:**
- Produces: `extract_youtube_video_id(url: str) -> str`
- Produces: `LearningPath`, `Course`, and `CourseModule`
- Produces: `CourseModule.youtube_embed_url(origin: str) -> str`

- [ ] Write tests proving supported YouTube watch, short, and embed URLs normalize to an ID; unsupported hosts and malformed IDs fail validation.
- [ ] Run `python manage.py test apps.academy.tests.test_models` and verify the missing app/model failure.
- [ ] Implement the app, validator, and models with database ordering/uniqueness constraints.
- [ ] Generate `0001_initial.py` and inspect it for only Academy tables.
- [ ] Re-run the focused tests and `python manage.py makemigrations --check --dry-run`.

### Task 2: Admin authoring experience

**Files:**
- Create: `apps/academy/admin.py`
- Create: `apps/academy/tests/test_admin.py`

**Interfaces:**
- Consumes: `LearningPath`, `Course`, `CourseModule`
- Produces: registered list/filter/search admin screens and ordered `CourseModuleInline`

- [ ] Write tests proving a staff superuser can open path/course admin pages and that invalid YouTube URLs are rejected through model validation.
- [ ] Run the focused admin tests and verify failure because models are not registered.
- [ ] Register paths and courses, use module inlines, and expose publication/order filters.
- [ ] Re-run focused model/admin tests.

### Task 3: Published catalogue API

**Files:**
- Create: `apps/academy/serializers.py`
- Create: `apps/academy/api_views.py`
- Create: `apps/academy/tests/test_api.py`
- Modify: `apps/api/urls.py`

**Interfaces:**
- Produces: `GET /api/v1/academy/paths/`
- Produces: `GET /api/v1/academy/courses/`
- Produces: `GET /api/v1/academy/courses/<slug>/`
- Course detail returns ordered published modules with `video_embed_url` generated for the current origin.

- [ ] Write authenticated API tests for published filtering, path filtering, ordering, anonymous denial, and origin-aware YouTube embed output.
- [ ] Run the API tests and verify 404/missing serializer failures.
- [ ] Implement read-only serializers/viewsets and register router paths.
- [ ] Re-run API tests for both `/api/v1/` and the legacy `/api/` include without adding frontend dependence on the legacy path.

### Task 4: Seed the prototype course catalogue

**Files:**
- Create: `apps/academy/management/__init__.py`
- Create: `apps/academy/management/commands/__init__.py`
- Create: `apps/academy/management/commands/seed_academy.py`
- Create: `apps/academy/tests/test_seed_command.py`

**Interfaces:**
- Produces: idempotent `python manage.py seed_academy`
- Consumes: the approved sample titles/content formerly held in `SMEs (3)/SMEs/academy/js/data.js`

- [ ] Write a test that runs the command twice and asserts stable path/course/module counts and updated content rather than duplicates.
- [ ] Run it and verify the missing-command failure.
- [x] Implement deterministic `get_or_create` seeding with stable slugs and publish flags so reruns preserve administrator edits.
- [ ] Re-run the seed test and inspect a seeded course/module through the ORM.

### Task 5: Django Academy course page

**Files:**
- Create: `apps/academy/views.py`
- Create: `apps/academy/urls.py`
- Create: `apps/academy/tests/test_views.py`
- Create: `templates/academy/index.html`
- Create: `static/sme/academy/js/api.js`
- Create: `static/sme/academy/js/course-page.js`
- Copy unchanged then reference: `static/sme/shared/css/inventory.css`
- Copy unchanged then reference: `static/sme/shared/css/knowledge-hub.css`
- Copy unchanged then reference: `static/sme/academy/css/style.css`
- Modify: `jbs_crm/urls.py`

**Interfaces:**
- Produces: authenticated `/academy/` with course list and `#course/<slug>` detail routing
- Consumes: `/api/v1/academy/paths/`, `/api/v1/academy/courses/`, and course detail

- [ ] Write view tests for authentication, static assets, page-specific `frame-src` CSP, and absence of a `data.js` script.
- [ ] Run view tests and verify missing route failure.
- [ ] Add the route/template and preserved stylesheet references.
- [ ] Implement fetch/loading/error/empty states and client-side list/detail rendering.
- [ ] Render YouTube modules as sandboxed, titled iframes using only API-produced embed URLs.
- [ ] Run view/API tests and Django `check`.

### Task 6: End-to-end verification and documentation

**Files:**
- Modify: `Master Plan.md`
- Modify: `SMEs (3)/SMEs/academy/README.md`

**Interfaces:**
- Documents: admin authoring, seed command, supported YouTube URL forms, and course page URLs.

- [ ] Apply migrations to the development database and run `seed_academy`.
- [ ] Run `python manage.py test` and confirm zero failures.
- [ ] Run `python manage.py makemigrations --check --dry-run` and `python manage.py check`.
- [ ] Start Django and verify the authenticated course list/detail journey when the in-app browser is available.
- [ ] Update documentation with actual completed behavior and remaining Academy features.
