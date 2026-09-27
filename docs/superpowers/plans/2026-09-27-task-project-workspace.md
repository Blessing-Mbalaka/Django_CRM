# Task and Project Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Kanban-only task page with the complete prototype-matched, database-backed task and project workspace.

**Architecture:** Preserve the existing Board, Project, Task, notification, comment, and activity models while standardizing board columns through a data migration and adding project lifecycle fields plus protected attachment records. Serve one Django task shell at `/tasks/`, use hash routing for all reference screens, and fetch accessible persisted data through explicit DRF endpoints and focused query/services.

**Tech Stack:** Django 6.0, Django REST Framework 3.17, vanilla ES modules, native `<dialog>`, Django TestCase/APITestCase, Playwright

**Spec:** `docs/superpowers/specs/2026-09-27-academy-tasks-inventory-integration-design.md`

## Global Constraints

- Task boards have exactly `To Do`, `In Progress`, and `Completed`, in that order.
- Existing task IDs, assignments, parents, projects, and activity history must survive migration.
- Overdue is calculated and is never a stored fourth status.
- Weeks run Monday through Sunday; calendar grids are Monday-first and six weeks long.
- Attachments are real authenticated uploads, maximum 25 MB, using the existing document MIME allowlist.
- The live app uses Django data only; prototype sample data is never imported.
- The workspace returns to `/academy/#tools` and uses its own prototype-matched responsive shell.

## Review Focus

- Unknown custom board columns must migrate to `In Progress`, never falsely complete work.
- Merging multiple source columns must produce stable contiguous positions ordered by original column position, task position, then task ID.
- An assignee who can see a task must not gain access to another task's attachment by changing an ID.
- Calendar date-range inputs larger than 62 days or malformed dates must return 400 rather than an unbounded query.
- Task/project counts must not double-count records reached through multiple access relationships.

---

### Task 1: Add project lifecycle fields and canonicalize board columns

**Files:**
- Modify: `apps/tasks/models.py`
- Create: `apps/tasks/migrations/0003_project_lifecycle_taskattachment_three_state.py`
- Modify: `apps/tasks/tests.py`

**Interfaces:**
- Consumes: existing `Board`, `BoardColumn`, `Project`, and `Task` records
- Produces: `Project.Status`, `Project.start_date`, `Project.status`, and exactly three canonical columns per board

- [ ] **Step 1: Write migration and model tests**

Add tests named `test_new_project_defaults_to_planning_with_start_date`, `test_project_rejects_due_date_before_start_date`, `test_new_board_has_exact_three_columns`, and a `TransactionTestCase` migration test that creates all five legacy columns plus a custom `Review` column and asserts the mapping, stable task IDs, contiguous positions, parent links, and activities after migration.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskLifecycleModelTests apps.tasks.tests.TaskThreeStateMigrationTests -v 2`

Expected: FAIL because lifecycle fields and migration do not exist and board creation still yields five columns.

- [ ] **Step 3: Implement model fields and validation**

Add `Project.Status` choices `planning`, `active`, `on_hold`, `completed`; add `start_date: DateField(default=timezone.localdate)` and `status: CharField(...)`; implement `Project.clean()` to reject `due_date < start_date`.

- [ ] **Step 4: Implement the data migration**

In `0003...`, add the project fields and a `RunPython` operation. For each board, create temporary canonical destinations, order source tasks by source-column position/task position/ID, map Backlog and To Do to To Do, In Progress/Blocked/unknown columns to In Progress, Done/Completed to Completed, rewrite positions, then remove superseded columns and finalize canonical names/positions.

- [ ] **Step 5: Change new-board defaults**

Update `BoardViewSet.perform_create()` in `apps/tasks/api_views.py` to create only the three canonical columns.

- [ ] **Step 6: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskLifecycleModelTests apps.tasks.tests.TaskThreeStateMigrationTests apps.tasks.tests.TaskApiTests -v 2`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add apps/tasks/models.py apps/tasks/migrations/0003_project_lifecycle_taskattachment_three_state.py apps/tasks/api_views.py apps/tasks/tests.py
git commit -m "feat: standardize task workflow states"
```

### Task 2: Synchronize completion and project updates

**Files:**
- Modify: `functionalities/tasks/services.py`
- Modify: `functionalities/tasks/validators.py`
- Modify: `apps/tasks/serializers.py`
- Modify: `apps/tasks/api_views.py`
- Modify: `apps/tasks/tests.py`

**Interfaces:**
- Consumes: `move_task(*, task, destination, position, actor) -> Task`
- Produces: synchronized `completed_at`; writable project lifecycle fields; `ProjectSerializer.validate(attrs)`

- [ ] **Step 1: Write failing service and API tests**

Add `test_move_to_completed_sets_completed_at`, `test_move_out_of_completed_clears_completed_at`, `test_project_due_date_must_not_precede_start`, and `test_owner_can_update_project_lifecycle`. Assert persisted model state.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskCompletionTests apps.tasks.tests.ProjectLifecycleApiTests -v 2`

Expected: FAIL because completion is not synchronized and projects are create/read-only through the API.

- [ ] **Step 3: Implement completion synchronization**

Update `move_task` so a destination named `Completed` sets `completed_at=timezone.now()` only when empty; any other destination clears it. Include `completed_at` in `update_fields` and retain the activity record.

- [ ] **Step 4: Expose validated project lifecycle updates**

Add `start_date` and `status` to `ProjectSerializer`; validate date ordering using the instance values on partial update; allow `patch`/`put` in `ProjectViewSet.http_method_names`; restrict mutation queryset to the board owner.

- [ ] **Step 5: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskCompletionTests apps.tasks.tests.ProjectLifecycleApiTests -v 2`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add functionalities/tasks/services.py functionalities/tasks/validators.py apps/tasks/serializers.py apps/tasks/api_views.py apps/tasks/tests.py
git commit -m "feat: persist task and project lifecycle"
```

### Task 3: Add protected genuine task attachments

**Files:**
- Modify: `apps/tasks/models.py`
- Modify: `apps/tasks/migrations/0003_project_lifecycle_taskattachment_three_state.py`
- Create: `functionalities/tasks/attachments.py`
- Modify: `apps/tasks/serializers.py`
- Modify: `apps/tasks/api_views.py`
- Modify: `apps/tasks/views.py`
- Modify: `apps/tasks/urls.py`
- Modify: `apps/api/urls.py`
- Modify: `apps/tasks/tests.py`

**Interfaces:**
- Consumes: `functionalities.documents.validators.validate_upload(upload)` and task-access query rules
- Produces: `TaskAttachment`, `add_task_attachment(*, task, upload, user) -> TaskAttachment`, `TaskAttachmentViewSet`, and `download_attachment(request, pk)`

- [ ] **Step 1: Write failing upload/access tests**

Using `override_settings(MEDIA_ROOT=tempdir)`, add separate tests for accepted text upload metadata/checksum, rejection over 25 MB, rejection of an unsupported MIME type, owner download, assigned-user download, unrelated-user 404, and deletion removing the stored file.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskAttachmentTests -v 2`

Expected: FAIL because attachment interfaces do not exist.

- [ ] **Step 3: Add the attachment model and service**

Define `task_attachment_upload_path(instance, filename)` and `TaskAttachment` with the exact metadata from the spec. Implement `add_task_attachment` to call `validate_upload`, hash chunks with SHA-256, reset the stream, and save inside `transaction.atomic()`.

- [ ] **Step 4: Add DRF upload/list/delete and protected download**

Add `TaskAttachmentSerializer` and `TaskAttachmentViewSet` using multipart parsing and an accessible-task queryset shared through a helper. Register `task-attachments`. Add `download_attachment` using `FileResponse` with sanitized download name and return 404 outside the accessible queryset.

- [ ] **Step 5: Run attachment tests**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskAttachmentTests -v 2`

Expected: PASS with temporary media cleanup.

- [ ] **Step 6: Commit**

```powershell
git add apps/tasks functionalities/tasks apps/api/urls.py
git commit -m "feat: add protected task attachments"
```

### Task 4: Add bounded task workspace query endpoints

**Files:**
- Create: `functionalities/tasks/queries.py`
- Modify: `apps/tasks/api_views.py`
- Modify: `apps/tasks/serializers.py`
- Modify: `apps/tasks/tests.py`

**Interfaces:**
- Produces: `accessible_boards(user) -> QuerySet`, `accessible_tasks(user) -> QuerySet`, `accessible_projects(user) -> QuerySet`, `dashboard_summary(user) -> dict`, `calendar_items(user, start, end) -> dict`, and `team_summary(user) -> list[dict]`
- Produces DRF actions: `GET /api/v1/tasks/dashboard/`, `GET /api/v1/tasks/calendar/?start=&end=`, and `GET /api/v1/tasks/team/`

- [ ] **Step 1: Write failing query/API tests**

Add individual tests for deduplicated dashboard counts, Monday/Sunday due items, calendar project/task payloads, malformed dates, a range over 62 days, accessible team aggregation, and exclusion of an unrelated board's data.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskWorkspaceQueryTests -v 2`

Expected: FAIL with missing actions/functions.

- [ ] **Step 3: Implement shared accessible querysets**

Move repeated ownership/assignment `Q` expressions into the three query helpers and use `.distinct()` consistently. Refactor existing task viewsets to consume them without changing permissions.

- [ ] **Step 4: Implement summaries and bounded calendar action**

Return ISO dates, integer counts, and existing serializer-compatible IDs. Validate both dates, require `start <= end`, and reject spans above 62 days with HTTP 400.

- [ ] **Step 5: Run query tests and existing task API tests**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests -v 2`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add functionalities/tasks/queries.py apps/tasks/api_views.py apps/tasks/serializers.py apps/tasks/tests.py
git commit -m "feat: expose task workspace summaries"
```

### Task 5: Build the prototype-matched task shell and hash router

**Files:**
- Replace: `templates/tasks/board.html`
- Remove include usage from: `templates/tasks/partials/_projects.html`
- Create: `static/sme/tasks/css/style.css`
- Create: `static/sme/tasks/js/api.js`
- Create: `static/sme/tasks/js/views.js`
- Create: `static/sme/tasks/js/app.js`
- Modify: `apps/tasks/views.py`
- Modify: `apps/tasks/tests.py`

**Interfaces:**
- Consumes: named endpoint configuration, authenticated user/permissions, and Tasks API from Tasks 2–4
- Produces: hash routes `dashboard`, `projects`, `project/<id>`, `tasks`, `my`, `calendar`, and `team`

- [ ] **Step 1: Write failing shell/template tests**

Assert `/tasks/` contains the task workspace shell, seven navigation routes with prototype labels/icons, `/academy/#tools`, sign-out form, native dialog, safely serialized configuration, and no generic `base.html` topbar markers.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests.TaskWorkspaceTemplateTests -v 2`

Expected: FAIL against the current Kanban-only Bootstrap template.

- [ ] **Step 3: Build the Django shell and static styling**

Port the supplied task and shared inventory visual rules into maintained `static/sme/tasks/css/style.css`, using Django static asset URLs for the banner. Render endpoint/user/permission configuration with `json_script`.

- [ ] **Step 4: Implement the API adapter**

In `api.js`, provide named methods for boards, projects, tasks, summaries, calendar, team, and attachments. Use the existing CSRF-aware request client behavior and multipart `FormData` for files.

- [ ] **Step 5: Implement views and routing**

In `views.js`, implement renderers for all seven screens and forms. In `app.js`, implement hash parsing, active navigation/icons, conditional primary actions, state refresh, dialogs, filters, three-state movement, calendar controls, task/project CRUD, completion, and upload handling.

- [ ] **Step 6: Run template and task tests**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests -v 2`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add templates/tasks static/sme/tasks apps/tasks/views.py apps/tasks/tests.py
git commit -m "feat: build complete task workspace"
```

### Task 6: Add task browser acceptance coverage

**Files:**
- Create: `tests/browser/test_task_workspace.py`
- Modify: `tests/browser/test_dummy_users.py`

**Interfaces:**
- Consumes: live Django server and demo users
- Produces: repeatable desktop/mobile acceptance journey with uniquely prefixed fixtures

- [ ] **Step 1: Write the failing browser journey**

Cover login, seven hash routes, responsive sidebar, project create/detail, task create/edit, list/board filters, three-state move, My Tasks filters, calendar month change, team metrics, attachment upload/download, access denial for an unrelated user, and cleanup/archive of created fixtures. Capture page errors and HTTP 500 responses.

- [ ] **Step 2: Run against the development server and verify RED**

Run server: `.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`

Run: `.venv\Scripts\python.exe tests/browser/test_task_workspace.py`

Expected: FAIL at the first missing workspace behavior before frontend implementation is complete; after Task 5 it should identify any integration gap.

- [ ] **Step 3: Fix only browser-discovered integration defects through a failing Django or browser assertion**

Keep production changes scoped to the failed acceptance behavior and rerun its focused automated test first.

- [ ] **Step 4: Run task and browser suites**

Run: `.venv\Scripts\python.exe manage.py test apps.tasks.tests -v 2`

Run: `.venv\Scripts\python.exe tests/browser/test_task_workspace.py`

Expected: PASS with no page errors or HTTP 500 responses.

- [ ] **Step 5: Commit**

```powershell
git add tests/browser/test_task_workspace.py tests/browser/test_dummy_users.py apps/tasks functionalities/tasks templates/tasks static/sme/tasks
git commit -m "test: cover task workspace journeys"
```

