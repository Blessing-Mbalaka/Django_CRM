# Academy Management Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a protected, SME-branded Academy workspace where authorised managers can CRUD all administrator-configured Academy content without relying on Django Admin.

**Architecture:** Add explicit management APIs under `/api/v1/academy/manage/`, backed by dedicated serializers, viewsets, permission checks and safe-removal services. Inject endpoint metadata into the existing Academy shell and use separate vanilla-JavaScript modules plus native dialogs for management lists, forms, nested editors and funding CSV ingestion; learner APIs remain read-only.

**Tech Stack:** Django 5, Django REST Framework, Django ORM, vanilla JavaScript, native `<dialog>`, existing SME CSS, Django TestCase/APITestCase, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-18-academy-management-workspace-design.md`

## Global Constraints

- Allow superusers, Django staff, role `admin`, and role `dean`; deny ordinary users in the backend and hide their controls.
- Preserve learner history. Referenced content is archived/unpublished, never cascade-deleted.
- Keep learner APIs read-only and restricted to active/published content.
- Never hardcode hosts, ports, endpoint paths or CSRF tokens in frontend JavaScript.
- Keep funding CSV preview/import atomic and reuse `FUNDING_CSV_HEADERS` plus `import_funding_csv`.
- Use locally styled native dialogs; do not depend on Bootstrap CDN behavior.
- Do not expose writes for enrolments, progress, attempts, certificates, submissions, registrations, bookings, conversations or messages.
- Preserve all unrelated workspace changes.

## File Map

**Create:**

- `apps/academy/permissions.py` — manager predicate and DRF permission.
- `apps/academy/management_services.py` — explicit safe delete/archive policy.
- `apps/academy/management_serializers.py` — write serializers for managed entities only.
- `apps/academy/management_views.py` — protected CRUD viewsets and CSV actions.
- `apps/academy/migrations/0005_diagnostic_children_is_active.py` — archive state for diagnostic children.
- `apps/academy/tests/test_management_permissions.py`
- `apps/academy/tests/test_safe_archive.py`
- `apps/academy/tests/test_management_api.py`
- `apps/academy/tests/test_management_funding.py`
- `apps/academy/tests/test_management_views.py`
- `static/sme/academy/js/academy-admin-api.js`
- `static/sme/academy/js/academy-admin-schema.js`
- `static/sme/academy/js/academy-admin.js`
- `static/sme/academy/css/admin.css`
- `tests/browser/test_academy_management.py`

**Modify:** `apps/academy/models.py`, `apps/academy/serializers.py`, `apps/academy/api_views.py`, `apps/api/urls.py`, `apps/academy/views.py`, `templates/academy/index.html`, `static/sme/academy/js/course-page.js`, `static/sme/academy/css/style.css`, `tests/browser/test_dummy_users.py`, `Master Plan.md`.

---

### Task 1: Management authority and navigation visibility

**Files:** Create `apps/academy/permissions.py`, `apps/academy/tests/test_management_permissions.py`; modify `apps/academy/views.py`, `templates/academy/index.html`.

**Produces:** `is_academy_manager(user) -> bool`, `IsAcademyManager(BasePermission)`, and template context `can_manage_academy`.

- [ ] **Write the failing permission/navigation test.** Create ordinary role-staff, role-admin, role-dean, Django-staff and superuser accounts. Assert only the first lacks `data-route="manage"`; later API tests will assert HTTP 403.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_permissions --verbosity 2`. Expected failure: management route absent for approved users.
- [ ] **Implement the permission:**

```python
MANAGER_ROLES = {'admin', 'dean'}

def is_academy_manager(user):
    return bool(user and user.is_authenticated and (
        user.is_superuser or user.is_staff or getattr(user, 'role', None) in MANAGER_ROLES
    ))

class IsAcademyManager(BasePermission):
    message = 'Academy management access is required.'
    def has_permission(self, request, view):
        return is_academy_manager(request.user)
```

- [ ] **Pass `can_manage_academy` into the template** and conditionally render one inline-SVG `Manage Academy` sidebar button.
- [ ] **Run GREEN:** repeat the Task 1 test; expect PASS.
- [ ] **Commit:** `git add` only Task 1 files, then `git commit -m "feat: gate academy management workspace"`.

---

### Task 2: Safe archive model state and service

**Files:** Create migration `0005`, `management_services.py`, `test_safe_archive.py`; modify `models.py`, `serializers.py`, `api_views.py`.

**Produces:** `RemovalResult(action, instance)` and `safe_remove(instance) -> RemovalResult`.

- [ ] **Write failing tests** proving: referenced course becomes unpublished while enrolment survives; event with registration becomes unpublished; mentor with booking becomes inactive; module with progress becomes unpublished; forum post becomes hidden; unused resource is hard-deleted; a question in a submitted diagnostic becomes inactive.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_safe_archive --verbosity 2`. Expected import/missing-field failures.
- [ ] **Add `is_active = models.BooleanField(default=True)`** to `DiagnosticQuestion`, `DiagnosticOption`, and `DiagnosticRecommendation`; create migration 0005.
- [ ] **Filter learner diagnostic output** so inactive questions, options and recommendations never appear.
- [ ] **Implement explicit safe-removal dispatch:** categories archive when referenced; paths archive when courses exist; courses archive when enrolments/recommendations exist; modules archive when progress/attempts exist; diagnostics and children archive when submissions exist; events archive when registrations exist; mentors archive when bookings exist; forum posts always hide; unreferenced resources/funding and other unreferenced records may delete.
- [ ] **Run GREEN and migration check:**

```powershell
.venv\Scripts\python.exe manage.py test apps.academy.tests.test_safe_archive apps.academy.tests.test_learning_features --verbosity 2
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

- [ ] **Commit:** Task 2 files with `git commit -m "feat: preserve academy history during removal"`.

---

### Task 3: Taxonomy and learning management APIs

**Files:** Create `management_serializers.py`, `management_views.py`, `test_management_api.py`; modify `apps/api/urls.py`.

**Consumes:** `IsAcademyManager`, `safe_remove`. **Produces:** manager-only ModelViewSets for course categories, levels, paths, courses and modules.

- [ ] **Write failing API tests**: ordinary user POST returns 403; each approved manager type can list; role-admin can create/PATCH/DELETE a category; duplicate slug returns keyed HTTP 400; archived records remain in management lists.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_api.AcademyTaxonomyManagementTests --verbosity 2`. Expected 404.
- [ ] **Implement serializers with exact fields:** categories/levels `id,name,slug,position,is_active`; paths `id,slug,title,description,business_stage,position,is_published,created_at,updated_at`.
- [ ] **Implement `SafeDestroyModelViewSet`** returning HTTP 200 `{'action':'archived','item':...}` for archive or HTTP 204 for delete.
- [ ] **Register exact prefixes:** `academy/manage/course-categories`, `course-levels`, `paths`.
- [ ] **Write failing learning tests** for course fields `path,category,level_config,slug,title,description,learning_outcome,instructor_name,level,duration_minutes,passing_grade,certificate_enabled,position,is_published`; test position uniqueness. Test module video validation and quiz options/correct index.
- [ ] **Implement course/module serializers and viewsets.** Expose relation IDs for writes and read-only relation summaries. Convert Django `full_clean()` errors into DRF field errors.
- [ ] **Register:** `academy/manage/courses` and `academy/manage/modules`; filter modules by `course` query parameter.
- [ ] **Run GREEN:**

```powershell
.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_api apps.academy.tests.test_api apps.academy.tests.test_learning_features --verbosity 2
```

- [ ] **Commit:** management API files with `git commit -m "feat: add academy learning management APIs"`.

---

### Task 4: Diagnostic management and atomic children

**Files:** Modify `management_serializers.py`, `management_views.py`, `test_management_api.py`, `apps/api/urls.py`.

**Produces:** CRUD for diagnostic categories, diagnostics, questions, options, recommendations; `POST diagnostics/{id}/replace-children/`.

- [ ] **Write failing CRUD tests** for fields: category `id,name,slug,position,is_active`; diagnostic `id,slug,title,version,is_published`; question `id,diagnostic,category,prompt,position,is_active`; option `id,question,label,score,position,is_active`; recommendation `id,diagnostic,category,course,minimum_score,maximum_score,message,position,is_active`.
- [ ] **Write failing rollback test:** submit valid questions plus recommendation with max below min to `replace-children`; expect HTTP 400 and original children unchanged.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_api.AcademyDiagnosticManagementTests --verbosity 2`. Expected 404.
- [ ] **Implement serializers** calling model validation and viewsets filtered by `diagnostic`/`question`.
- [ ] **Implement atomic replacement:** validate every nested serializer before mutating; use `transaction.atomic()`; preserve existing rows on any error.
- [ ] **Register all five prefixes** under `academy/manage/`.
- [ ] **Run GREEN plus learner scoring regression:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_api.AcademyDiagnosticManagementTests apps.academy.tests.test_extended_features --verbosity 2`.
- [ ] **Commit:** `git commit -m "feat: manage academy diagnostics safely"`.

---

### Task 5: Remaining content management APIs

**Files:** Modify `management_serializers.py`, `management_views.py`, `test_management_api.py`, `apps/api/urls.py`.

**Produces:** CRUD for resource/opportunity/event/forum categories, resources, funding, events, mentors; moderation-only forum posts.

- [ ] **Write failing table-driven CRUD tests** using these exact writable fields:

| Entity | Writable fields |
|---|---|
| Resource | `category,slug,title,description,resource_file,external_url,is_published` |
| Funding | `category,slug,title,provider,description,eligibility,opens_on,closes_on,application_url,contact_email,is_published` |
| Event | `category,slug,title,description,starts_at,ends_at,capacity,venue,meeting_url,registration_url,is_published` |
| Mentor | `user,expertise,industries,biography,availability,is_active` |
| Each category | `name,slug,position,is_active` |

- [ ] **Add failing validation tests** for multipart resource upload, funding close-before-open, event end-before-start, and mentor user change after a booking.
- [ ] **Add failing forum moderation test:** manager may change only `status,is_pinned,is_locked`; `author,title,body` remain read-only.
- [ ] **Run RED:** targeted `AcademyContentManagementTests`; expect 404.
- [ ] **Implement explicit serializers/viewsets** and route prefixes `resource-categories`, `resources`, `opportunity-categories`, `funding`, `event-categories`, `events`, `mentors`, `forum-categories`, `forum-posts`.
- [ ] **Run GREEN and learner regressions:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_api apps.academy.tests.test_api apps.academy.tests.test_extended_features --verbosity 2`.
- [ ] **Commit:** `git commit -m "feat: add academy content management APIs"`.

---

### Task 6: Funding CSV management actions

**Files:** Create `test_management_funding.py`; modify `management_views.py`, `funding_import.py` only if required, and `apps/api/urls.py`.

**Produces:** `GET funding/csv-template/`, `POST funding/preview-csv/`, `POST funding/import-csv/`.

- [ ] **Write failing tests** for exact template header/content disposition, preview without writes, valid import count/writes, invalid mixed upload with zero writes, and ordinary-user 403.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_funding --verbosity 2`. Expected 404.
- [ ] **Implement DRF actions** on funding viewset using the existing constants/parser. Return `rows,errors,imported,is_valid`; do not duplicate CSV parsing rules.
- [ ] **Run GREEN plus Django Admin import regression:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_funding apps.academy.tests.test_admin --verbosity 2`.
- [ ] **Commit:** `git commit -m "feat: expose protected funding CSV workflow"`.

---

### Task 7: Management page, API client and simple native dialogs

**Files:** Create `academy-admin-api.js`, `academy-admin-schema.js`, `academy-admin.js`, `admin.css`, `test_management_views.py`; modify `views.py`, `index.html`, `course-page.js`.

**Produces:** `window.AcademyAdmin` with `render()`, `open(entityKey,id=null)`, `canManage`; JSON `#academy-management-data` shaped `{can_manage,endpoints,choices}`.

- [ ] **Write failing view tests:** manager HTML contains management CSS/scripts, JSON, dialog and canonical management URLs; ordinary HTML contains none.
- [ ] **Run RED:** `.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_views --verbosity 2`.
- [ ] **Inject reversed endpoints and choices** for business stages, legacy course levels, module types and forum statuses through `json_script` only for authorised users.
- [ ] **Add native dialog markup** with title, accessible error region, body, Cancel and Save; load scripts in API → schema → admin → course-page order.
- [ ] **Implement `academy-admin-api.js`:** read CSRF cookie, distinguish JSON/FormData, normalize DRF errors into `error.fields`, retain HTTP status.
- [ ] **Implement schemas** with exact list columns/form fields for simple entities; relation fields declare their option endpoint; dates and booleans use native controls.
- [ ] **Implement route/list/modal lifecycle:** seven groups, search/status filter, Add/Edit/Publish/Archive actions, pending-state prevention, inline errors, refresh and toast.
- [ ] **Delegate `#manage` from `course-page.js`** to `AcademyAdmin.render()`; deny non-manager route access.
- [ ] **Run GREEN and syntax checks:**

```powershell
.venv\Scripts\python.exe manage.py test apps.academy.tests.test_management_views apps.academy.tests.test_views --verbosity 2
node --check static/sme/academy/js/academy-admin-api.js
node --check static/sme/academy/js/academy-admin-schema.js
node --check static/sme/academy/js/academy-admin.js
node --check static/sme/academy/js/course-page.js
```

- [ ] **Commit:** `git commit -m "feat: add academy management workspace"`.

---

### Task 8: Contextual controls and complex editors

**Files:** Modify `academy-admin.js`, `course-page.js`, `admin.css`, `test_management_views.py`.

**Produces:** `openCourseEditor(id)`, `openDiagnosticEditor(id)`, `openFundingImport()` and shared `data-manage-*` actions.

- [ ] **Write failing view/UI-contract tests** asserting manager-only hooks for add course/resource/diagnostic/funding/event/mentor and category management.
- [ ] **Run RED:** targeted management-view test.
- [ ] **Render contextual controls** in Courses, Resources, Diagnostics, Funding, Events, Mentorship and Community; delegate every button to the shared module.
- [ ] **Implement course editor:** parent fields; ordered module list; conditional video/resource fields; repeatable quiz options and correct-option radio; module Add/Edit/Archive.
- [ ] **Implement diagnostic editor:** parent fields; ordered questions and scored options; recommendation rules; save children through atomic `replace-children`.
- [ ] **Implement funding CSV dialog:** download template, choose file, preview errors/rows, enable Import only when valid, refresh management and learner funding on success.
- [ ] **Run GREEN:** management view/API/funding tests and JavaScript syntax checks.
- [ ] **Commit:** `git commit -m "feat: manage academy content from contextual dialogs"`.

---

### Task 9: Browser acceptance, documentation and full verification

**Files:** Create `tests/browser/test_academy_management.py`; modify `test_dummy_users.py`, `Master Plan.md`.

- [ ] **Write failing Playwright manager journey:** sign in as `mradebe`; open `#manage`; assert seven groups/native dialog; create/edit resource category; create/publish resource; verify in `#resources`; archive and verify absent; preview controlled funding CSV; assert canonical URLs/no page errors/no HTTP 500.
- [ ] **Add ordinary-user journey:** `zmahlangu` cannot see management controls and direct management API returns 403.
- [ ] **Run RED:** `$env:CRM_TEST_BASE_URL='http://127.0.0.1:8023'; .venv\Scripts\python.exe tests\browser\test_academy_management.py`.
- [ ] **Fix each integration defect test-first** with the smallest relevant regression test before implementation.
- [ ] **Update Master Plan** with permission boundary, entity matrix, safe archive, modal CRUD, funding CSV and deferred Tasks audit.
- [ ] **Run full verification:**

```powershell
.venv\Scripts\python.exe manage.py test --verbosity 1
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
node --check static/sme/academy/js/api.js
node --check static/sme/academy/js/course-page.js
node --check static/sme/academy/js/academy-admin-api.js
node --check static/sme/academy/js/academy-admin-schema.js
node --check static/sme/academy/js/academy-admin.js
$env:CRM_TEST_BASE_URL='http://127.0.0.1:8023'; .venv\Scripts\python.exe tests\browser\test_dummy_users.py
$env:CRM_TEST_BASE_URL='http://127.0.0.1:8023'; .venv\Scripts\python.exe tests\browser\test_academy_management.py
git diff --check
```

- [ ] **Review final diff:** confirm every management view uses `IsAcademyManager`, no learner record serializer is writable, all JS endpoints are injected, and unrelated changes remain untouched.
- [ ] **Commit acceptance artifacts:** `git commit -m "test: verify academy management workspace"` with only browser tests and Master Plan staged.
