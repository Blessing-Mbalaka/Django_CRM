# CRM Application Bundling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce Academy to six ordered application launchers, move every other authenticated tool into a role-aware CRM sidebar, and verify the migrated Marketing workspace and its five official provider adapters.

**Architecture:** Split the server-owned navigation registry into an Academy projection and a grouped CRM projection while preserving every existing canonical route. Render a Project Management-style CRM sidebar through the shared base template only for namespaces belonging to the CRM bundle; standalone application shells remain independent.

**Tech Stack:** Python 3.12, Django 6.0.4, Django templates, vanilla JavaScript, CSS, Django `TestCase`, Playwright

**Spec:** `docs/superpowers/specs/2026-10-16-crm-application-bundling-design.md`

## Global Constraints

- Academy must show exactly: Invoicing, Inventory, Project Management, Marketing, CRM, Documents, in that order.
- Preserve all canonical Django routes, models, records, and existing permission checks.
- Every non-primary tool must be discoverable from CRM, subject to its current role rule.
- Billing, Inventory, Tasks, Marketing, Documents, and Academy must remain standalone applications and must not receive the CRM sidebar.
- Reuse the existing Marketing provider implementation and environment-variable names; do not add a second provider layer.
- Never expose provider secrets or make live external provider calls in tests.
- Preserve the user's existing uncommitted changes in `templates/academy/index.html`, `apps/academy/tests/test_views.py`, `Master Plan.md`, `ReadME`, `docs/release-checklist.md`, and `docs/uat/`.

## Review Focus

- A route with a nested or legacy namespace must not incorrectly lose or gain the CRM shell; Task 3 tests both CRM and standalone namespace sets.
- A user with an empty/unknown role must still receive all non-privileged CRM links but never Payroll or System Admin; Task 1 adds this case.
- Two navigation entries that share an endpoint, such as Business Activity and Reports, must remain distinct labeled links; Task 1 asserts labels as well as URLs.
- A mobile sidebar opened and then followed must close and restore truthful `aria-expanded` state; Task 3 covers and exercises the behavior in a browser.
- Marketing with no provider credentials must load with five independent `not_configured` states and no secret values; Task 4 runs the existing provider/API coverage and checks the migrated local schema.

---

### Task 1: Split the Canonical Navigation Registry

**Files:**
- Create: `apps/core/test_navigation.py`
- Modify: `functionalities/crm_core/navigation.py`

**Interfaces:**
- Consumes: Django user objects and existing named URL routes.
- Produces: `get_academy_primary_tools(user) -> list[dict]`, `get_crm_navigation(user) -> list[dict]`, and a backward-compatible `get_suite_navigation(user) -> list[dict]` for callers not yet migrated.

- [ ] **Step 1: Write failing tests for the six primary tools**

Add `NavigationRegistryTests.test_primary_tools_have_exact_order_labels_and_routes` with literal expectations:

```python
expected = [
    ('Invoicing', '/billing/'),
    ('Inventory', '/inventory/'),
    ('Project Management', '/tasks/'),
    ('Marketing', '/growth/'),
    ('CRM', '/clients/'),
    ('Documents', '/documents/'),
]
self.assertEqual([(item['label'], item['url']) for item in get_academy_primary_tools(self.user)], expected)
```

Assert that the returned records retain `description` and `svg_path` for the existing Academy card contract.

- [ ] **Step 2: Write failing tests for complete grouped CRM membership and role filtering**

Add separate tests asserting the literal group labels and ordered item labels from spec section 3.2. Assert distinct `Business Activity` and `Reports & Analytics` records even though both resolve under Analytics. Assert a normal or unknown-role user lacks `Payroll Management` and `System Admin`, while an administrator receives both.

- [ ] **Step 3: Run the registry tests and verify RED**

Run: `./.venv/Scripts/python.exe manage.py test apps.core.test_navigation -v 2`

Expected: FAIL because `get_academy_primary_tools` and `get_crm_navigation` do not exist.

- [ ] **Step 4: Implement the two projections in `functionalities/crm_core/navigation.py`**

Define the exact functions from the Interfaces block. Centralize item construction with the existing `_item` and `_direct_item` helpers, keep URL reversal server-side, omit empty groups, and retain current Payroll/System Admin conditions. Keep `get_suite_navigation` compatible until Task 2 and Task 3 move consumers to the new projections.

- [ ] **Step 5: Run the registry tests and verify GREEN**

Run: `./.venv/Scripts/python.exe manage.py test apps.core.test_navigation -v 2`

Expected: PASS.

- [ ] **Step 6: Commit the registry change**

```bash
git add apps/core/test_navigation.py functionalities/crm_core/navigation.py
git commit -m "refactor: split primary and CRM navigation"
```

### Task 2: Render Only the Six Primary Applications in Academy

**Files:**
- Modify: `apps/academy/views.py`
- Modify: `apps/academy/tests/test_views.py`
- Create: `tests/browser/test_crm_navigation.py`
- Modify only if required for labels/order: `static/sme/academy/js/course-page.js`

**Interfaces:**
- Consumes: `get_academy_primary_tools(user) -> list[dict]` from Task 1.
- Produces: the unchanged `academy_tools` template context and `academy-tools-data` JSON contract containing exactly six ordered records.

- [ ] **Step 1: Write the failing Academy context test**

Add `test_business_tools_contains_only_six_ordered_primary_apps` and assert `response.context['academy_tools']` has the exact label/URL pairs from Task 1. Also assert secondary labels such as `Engagements`, `Accounting`, `Payroll Management`, `System Admin`, `Business Diagnostic`, and `API Explorer` are absent from that context list.

- [ ] **Step 2: Run the Academy test and verify RED**

Run: `./.venv/Scripts/python.exe manage.py test apps.academy.tests.test_views.AcademyCoursePageTests.test_business_tools_contains_only_six_ordered_primary_apps -v 2`

Expected: FAIL because `academy_index` currently flattens the full suite catalogue.

- [ ] **Step 3: Write and verify the failing Academy-order browser test**

Assert the six visible Business Tools card headings equal the exact ordered labels and that no secondary label appears as a card.

Run: `./.venv/Scripts/python.exe -m pytest tests/browser/test_crm_navigation.py -v`

Expected: FAIL because Academy still exposes the full catalogue.

- [ ] **Step 4: Change `academy_index` to consume `get_academy_primary_tools`**

Map the registry records to the current `academy_tools` keys without re-sorting them. Do not replace or reformat the user's large in-progress Academy template.

- [ ] **Step 5: Run Academy view tests and verify GREEN**

Run: `./.venv/Scripts/python.exe manage.py test apps.academy.tests.test_views -v 2`

Expected: PASS with the six-item order preserved in the JSON payload.

- [ ] **Step 6: Commit the Academy projection**

```bash
git add apps/academy/views.py apps/academy/tests/test_views.py tests/browser/test_crm_navigation.py static/sme/academy/js/course-page.js
git commit -m "feat: show six primary business applications"
```

Omit `static/sme/academy/js/course-page.js` from the commit if no change was needed.

### Task 3: Add the Persistent CRM Sidebar Shell

**Files:**
- Modify: `apps/core/context_processors.py`
- Modify: `apps/core/tests.py`
- Modify: `templates/base.html`
- Modify: `templates/partials/_navbar.html`
- Create: `templates/partials/_crm_sidebar.html`
- Create: `static/css/crm_shell.css`
- Create: `static/js/crm_shell.js`
- Modify: `tests/browser/test_crm_navigation.py`

**Interfaces:**
- Consumes: `get_crm_navigation(user) -> list[dict]` from Task 1 and `request.resolver_match.namespace`.
- Produces: context keys `crm_navigation: list[dict]`, `use_crm_shell: bool`, and `active_crm_namespace: str`; DOM IDs `crmSidebar`, `crmSidebarToggle`, and `crmMobileMenu`.

- [ ] **Step 1: Write failing shell-boundary tests**

Add tests that request `/clients/`, `/engagements/`, `/finance/`, and `/staff/` and assert the CRM sidebar, active navigation state, Business Tools return link, and sign-out form exist. Add tests that `/billing/` and `/documents/` do not contain `id="crmSidebar"`. Cover a legacy Centres namespace and an account/profile page so namespace classification cannot accidentally depend only on URL prefixes.

- [ ] **Step 2: Write failing context tests for unknown and privileged roles**

Assert `crm_navigation` excludes empty groups, a user with an unknown/blank role receives non-privileged links only, and an administrator receives Payroll and System Admin. Assert every link has `label`, `url`, and `svg_path`.

- [ ] **Step 3: Run the shell tests and verify RED**

Run: `./.venv/Scripts/python.exe manage.py test apps.core.tests.CEOApplicationSmokeTests apps.core.test_navigation -v 2`

Expected: FAIL because the CRM sidebar and context flags do not exist.

- [ ] **Step 4: Write and verify failing CRM-sidebar browser tests**

Open CRM, assert grouped secondary links, follow Engagements and confirm the CRM sidebar persists with the correct active entry. At a mobile viewport, open and close the drawer, follow a link, and assert the drawer closes and `aria-expanded="false"`.

Run: `./.venv/Scripts/python.exe -m pytest tests/browser/test_crm_navigation.py -v`

Expected: FAIL because the CRM sidebar DOM does not exist.

- [ ] **Step 5: Implement namespace classification and context**

In `apps/core/context_processors.py`, define `CRM_SHELL_NAMESPACES: frozenset[str]` for clients, engagements, sales, expenses, finance, accounting, analytics, products, purchasing, alerts, communication, ai, staff, centres/centres_legacy, payroll, and admin_panel. Produce the three context keys from the Interfaces block without changing endpoint authorization.

- [ ] **Step 6: Implement the CRM shell markup and styling**

Include `_crm_sidebar.html` from `base.html` only when `use_crm_shell` is true. Use grouped `<nav>` landmarks, server-rendered active state, inline SVG paths, a CSRF-protected logout form, and the Academy `#tools` return link. Add `crm_shell.css` and `crm_shell.js` only for the CRM shell; derive dimensions, collapsed rail, mobile drawer, focus states, and transitions from the existing Tasks/Project Management shell without importing Tasks application logic.

- [ ] **Step 7: Update the shared top bar for CRM shell coexistence**

Avoid duplicating the Business Tools return control when the sidebar is visible. Preserve notifications, alerts, user menu, and standalone Billing/Documents behavior.

- [ ] **Step 8: Run focused shell and smoke tests and verify GREEN**

Run: `./.venv/Scripts/python.exe manage.py test apps.core.tests apps.core.test_navigation -v 2`

Expected: PASS for CRM-contained and standalone routes.

- [ ] **Step 9: Run the CRM navigation browser tests and verify GREEN**

Run: `./.venv/Scripts/python.exe -m pytest tests/browser/test_crm_navigation.py -v`

Expected: PASS for Academy ordering, desktop navigation persistence, and mobile drawer behavior.

- [ ] **Step 10: Commit the CRM shell**

```bash
git add apps/core/context_processors.py apps/core/tests.py templates/base.html templates/partials/_navbar.html templates/partials/_crm_sidebar.html static/css/crm_shell.css static/js/crm_shell.js tests/browser/test_crm_navigation.py
git commit -m "feat: bundle secondary tools in CRM navigation"
```

### Task 4: Verify Marketing Migration and Provider Contracts

**Files:**
- Modify only if verification finds a real discrepancy: `.env.example`
- Modify only if verification finds a real discrepancy: `docs/marketing-provider-setup.md`
- Modify only if a missing regression is found: `apps/marketing/tests/test_provider_status.py`
- Modify only if a missing regression is found: `apps/marketing/tests/test_views.py`

**Interfaces:**
- Consumes: applied `marketing.0001_initial`, the existing `/growth/` shell, `/api/v1/marketing/workspace/provider-status/`, and environment-backed provider settings.
- Produces: evidence that the migrated workspace loads and five providers report safe independent status without network calls.

- [ ] **Step 1: Confirm migration and schema state without mutating it**

Run: `./.venv/Scripts/python.exe manage.py showmigrations marketing`

Expected: `[X] 0001_initial`.

Run: `./.venv/Scripts/python.exe manage.py shell -c "from django.db import connection; print(sorted(t for t in connection.introspection.table_names() if t.startswith('marketing_')))"`

Expected: the Marketing tables including campaigns, contacts, content, outbound messages, delivery attempts, and webhook events.

- [ ] **Step 2: Run the existing provider and Marketing workspace tests**

Run: `./.venv/Scripts/python.exe manage.py test apps.marketing.tests -v 2`

Expected: PASS without real external requests.

- [ ] **Step 3: Compare provider settings and setup links with official contracts**

Verify Twilio Email Basic Auth and asynchronous `operationId`, Twilio SMS sender-versus-Messaging-Service behavior, versioned Meta WhatsApp messages, Facebook Page publishing, and Instagram container/publish flow. If a discrepancy is found, first add a failing provider test, then make the smallest adapter or documentation correction and rerun the Marketing tests. If none is found, do not churn provider files.

- [ ] **Step 4: Verify the local Marketing route and provider-status API**

Using an authenticated local test user, confirm `/growth/` returns 200 and the provider-status endpoint returns five entries. With credentials absent, each affected entry must be `not_configured`; no response may contain an environment secret value.

- [ ] **Step 5: Commit only real corrections, if any**

```bash
git add .env.example docs/marketing-provider-setup.md apps/marketing/tests functionalities/marketing/providers
git commit -m "fix: align marketing provider configuration"
```

Skip this commit when verification requires no source change.

### Task 5: Browser and Whole-Application Regression

**Files:**
- No planned source changes; this task verifies the completed implementation.

**Interfaces:**
- Consumes: the six-card Academy JSON/UI, CRM sidebar DOM contract, existing authenticated test users, and canonical application URLs.
- Produces: end-to-end evidence for ordering, sidebar behavior, route continuity, responsive navigation, and clean application loading.

- [ ] **Step 1: Run the focused browser workspaces**

Run: `./.venv/Scripts/python.exe -m pytest tests/browser/test_crm_navigation.py tests/browser/test_academy_management.py tests/browser/test_marketing_workspace.py tests/browser/test_inventory_workspace.py tests/browser/test_task_workspace.py -v`

Expected: PASS, or report a named environment-only browser prerequisite separately.

- [ ] **Step 2: Run the complete Django suite**

Run: `./.venv/Scripts/python.exe manage.py test -v 2`

Expected: PASS. Report every pre-existing failure by exact test name; do not omit failures unrelated to this change.

- [ ] **Step 3: Run framework and migration checks**

Run: `./.venv/Scripts/python.exe manage.py check`

Expected: `System check identified no issues`.

Run: `./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run`

Expected: `No changes detected`.

- [ ] **Step 4: Stop and report verification**

Report the implemented grouping, Marketing migration/provider result, commands run, passing totals, any named pre-existing failures, and the files changed. Do not start a further restructuring phase.
