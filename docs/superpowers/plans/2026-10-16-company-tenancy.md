# Company Tenancy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce one-company-per-user data isolation across the entire SME Suite while allowing Django superusers to inspect and aggregate the full company ecosystem.

**Architecture:** A new `companies.Company` tenant root is referenced explicitly by users and every independently queryable business aggregate. Shared tenancy helpers scope REST and HTML querysets from the authenticated user, while child records scope through their tenant-owned parent. A staged migration assigns every legacy row to one generated default company before required constraints are enabled.

**Tech Stack:** Python 3, Django 6.0.4, Django REST Framework 3.17.1, SQLite, Django TestCase/APITestCase, browser acceptance scripts.

**Spec:** `docs/superpowers/specs/2026-10-16-company-tenancy-design.md`

## Global Constraints

- Each non-superuser belongs to exactly one active company; superusers may have no company and may access all companies.
- Tenant identity for normal users comes only from `request.user.company`, never request data, headers, or query parameters.
- Existing rows must be assigned to a generated default company without data loss.
- Cross-company object identifiers return not found for reads and validation errors for relationships/writes.
- Company-owned singletons and number sequences are unique per company, not global.
- Provider credentials remain deployment-level; provider messages and results are tenant-owned.
- Shared Academy catalogue content remains global; user activity is scoped through the user's company.
- Preserve unrelated working-tree changes and do not modify the embedded, uninstalled `apps/ProjectManagementAPP_FinalBoss` project.

## Review Focus

- A normal user submitting another company's foreign-key ID receives a validation error and no object is created.
- A normal user whose company is missing or inactive receives a denial, never an unrestricted queryset.
- A superuser without a company can list all tenants but must specify `company` when creating tenant-owned data through an API.
- Company-specific singleton loaders never reuse another company's `BrandKit` or `InventorySettings` row.
- Scheduled tasks and inbound webhooks update only the tenant-owned record identified by their explicit object/provider identifier.

---

### Task 1: Company foundation and tenant resolution

**Files:**
- Create: `apps/companies/__init__.py`
- Create: `apps/companies/apps.py`
- Create: `apps/companies/models.py`
- Create: `apps/companies/admin.py`
- Create: `apps/companies/tenancy.py`
- Create: `apps/companies/tests/__init__.py`
- Create: `apps/companies/tests/test_models.py`
- Create: `apps/companies/tests/test_tenancy.py`
- Modify: `jbs_crm/settings/base.py`
- Modify: `apps/accounts/models.py`
- Modify: `apps/accounts/admin.py`
- Modify: `apps/centres/models.py`
- Modify: `apps/centres/admin.py`

**Interfaces:**
- Produces: `Company`; `get_user_company(user) -> Company`; `require_user_company(user) -> Company`; `scope_queryset(queryset, user, company_lookup='company', requested_company_id=None) -> QuerySet`; `validate_same_company(company, **related_objects) -> None`.
- Produces: nullable `User.company` for superusers and required `Centre.company` in the final model state.

- [ ] **Step 1: Write failing company and tenancy tests**

Add tests proving company slugs are unique, centre name/code uniqueness is per company, non-superusers require an active company, inactive/missing companies are denied, normal-user querysets are scoped, superusers are unscoped, and cross-company relations fail `validate_same_company`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests -v 2`
Expected: FAIL because `apps.companies`, `Company`, and tenancy helpers do not exist.

- [ ] **Step 3: Implement the company foundation**

Create the model and helpers with the signatures above; register the app before tenant-owned local apps; add company fields and validation to `User` and `Centre`; expose company fields in Django Admin without changing role semantics.

- [ ] **Step 4: Create and inspect foundation migrations**

Run: `.venv\Scripts\python.exe manage.py makemigrations companies accounts centres`
Expected: new migrations for `Company`, `User.company`, `Centre.company`, and per-company centre constraints; no unrelated migration drift.

- [ ] **Step 5: Run focused tests and system checks**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests -v 2`
Expected: PASS.

Run: `.venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 6: Commit the foundation**

```bash
git add apps/companies apps/accounts/models.py apps/accounts/admin.py apps/accounts/migrations apps/centres/models.py apps/centres/admin.py apps/centres/migrations jbs_crm/settings/base.py
git commit -m "feat: add company tenant foundation"
```

### Task 2: Tenant ownership fields and legacy-data migration

**Files:**
- Create: `apps/companies/tests/test_migrations.py`
- Modify: `apps/clients/models.py`
- Modify: `apps/engagements/models.py`
- Modify: `apps/alerts/models.py`
- Modify: `apps/documents/models.py`
- Modify: `apps/tasks/models.py`
- Modify: `apps/billing/models.py`
- Modify: `apps/expenses/models.py`
- Modify: `apps/accounting/models.py`
- Modify: `apps/products/models.py`
- Modify: `apps/inventory/models.py`
- Modify: `apps/purchasing/models.py`
- Modify: `apps/sales/models.py`
- Modify: `apps/payroll/models.py`
- Modify: `apps/marketing/models.py`
- Create/Modify: migrations generated in each corresponding app's `migrations/` directory

**Interfaces:**
- Consumes: `Company` and Task 1 tenancy helpers.
- Produces: indexed `company` ownership on every independently queryable business aggregate and parent-path ownership for dependent records.
- Produces: `BrandKit.load(company)` and `InventorySettings.load(company)` with one row per company.

- [ ] **Step 1: Write failing ownership and migration tests**

Test the required ownership map:

- direct `company`: `Client`, `Engagement`, `Alert`, `DocumentLibrary`, `Board`, `NumberSequence`, `Invoice`, `ExpenseCategory`, `Expense`, `Account`, `AccountingPeriod`, `JournalEntry`, `BankStatement`, `Product`, `InventoryCategory`, `InventorySettings`, `StockLocation`, `StockMovement`, `Supplier`, `PurchaseSequence`, `PurchaseOrder`, `SalesSequence`, `SalesOrder`, `PayrollEmployee`, `PayRun`, `MarketingCampaign`, `MarketingContent`, `MarketingContact`, `MarketingLead`, `MarketingActivity`, `BrandKit`, `OutboundMessage`, and `ProviderWebhookEvent`;
- inherited through a required parent: finance records, communication logs, document folders/documents/versions/activity, board columns/tasks/projects/comments/activity/attachments/notifications, invoice lines/payments, expense approvals, journal lines/bank statement lines, reorder rules/product profiles, purchase-order descendants, sales-order descendants, payslips, adverts/metrics/delivery attempts, and Academy user activity.

Add migration-executor coverage that migrates representative legacy rows, confirms creation of slug `default-company`, confirms every new direct company field is populated, and confirms original row counts and relationships are unchanged.

- [ ] **Step 2: Run ownership tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_migrations apps.companies.tests.test_models -v 2`
Expected: FAIL because domain company fields and the backfill migration do not exist.

- [ ] **Step 3: Add ownership fields and company-scoped constraints**

Add the direct fields listed in Step 1. Replace global sequence keys, invoice numbers, product/location identifiers, categories, supplier identifiers, accounting identifiers, and singleton primary-key assumptions with company-scoped `UniqueConstraint` definitions where uniqueness is business-local.

Update `BrandKit.load(company)` and `InventorySettings.load(company)` to use `get_or_create(company=company)` and remove forced `pk=1` behavior. Update marketing/task/document upload functions to include `company.slug` or `company_id` in the path while retaining randomized or versioned filenames.

- [ ] **Step 4: Create staged schema and data migrations**

Generate nullable add-field migrations first. Add explicit `RunPython` operations using historical models to create `Default Company`/`default-company`, backfill users and every direct-owned row, and infer related ownership. Follow with non-null alterations and company-scoped constraints. Ensure migration dependencies respect `companies`, `accounts`, and cross-app foreign keys.

- [ ] **Step 5: Verify migration and ownership tests GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_migrations apps.companies.tests.test_models -v 2`
Expected: PASS.

Run: `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 6: Commit the tenant schema and backfill**

```bash
git add apps/*/models.py apps/*/migrations apps/companies/tests/test_migrations.py apps/companies/tests/test_models.py
git commit -m "feat: assign business data to companies"
```

### Task 3: Reusable REST tenancy enforcement

**Files:**
- Create: `apps/api/tenancy.py`
- Create: `apps/api/tests/__init__.py`
- Create: `apps/api/tests/test_tenancy.py`
- Modify: `apps/api/permissions.py`
- Modify: `apps/api/urls.py`

**Interfaces:**
- Consumes: `scope_queryset`, `require_user_company`, and `validate_same_company`.
- Produces: `ActiveCompanyRequired`; `TenantQuerySetMixin.company_lookup`; `TenantCreateMixin`; `TenantModelViewSet`; `TenantReadOnlyModelViewSet`; `get_request_company(request, require_for_write=False) -> Company | None`.

- [ ] **Step 1: Write failing generic API isolation tests**

Use two companies to prove the reusable viewset mixins scope list/detail/update/delete, assign company during create, reject body/query/header company overrides by normal users, deny inactive/missing-company users, allow a superuser to list all rows, and require a company selection for superuser writes.

- [ ] **Step 2: Run the tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.api.tests.test_tenancy -v 2`
Expected: FAIL because the tenancy API classes do not exist.

- [ ] **Step 3: Implement the REST tenancy layer**

Implement the interfaces above. Permit `?company=<pk>` only for superusers. Apply tenant filtering before all existing endpoint-specific filters and return 404 for cross-company detail URLs.

- [ ] **Step 4: Verify the generic layer GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.api.tests.test_tenancy -v 2`
Expected: PASS.

- [ ] **Step 5: Commit the REST tenancy layer**

```bash
git add apps/api/tenancy.py apps/api/permissions.py apps/api/urls.py apps/api/tests
git commit -m "feat: enforce tenant scope in REST primitives"
```

### Task 4: Scope every business API and relationship choice

**Files:**
- Modify: `apps/accounts/api_views.py`
- Modify: `apps/centres/api_views.py`
- Modify: `apps/clients/api_views.py`
- Modify: `apps/clients/serializers.py`
- Modify: `apps/staff/api_views.py`
- Modify: `apps/engagements/api_views.py`
- Modify: `apps/engagements/serializers.py`
- Modify: `apps/finance/api_views.py`
- Modify: `apps/alerts/api_views.py`
- Modify: `apps/communication/api_views.py`
- Modify: `apps/documents/api_views.py`
- Modify: `apps/documents/serializers.py`
- Modify: `apps/tasks/api_views.py`
- Modify: `apps/tasks/serializers.py`
- Modify: `apps/billing/api_views.py`
- Modify: `apps/billing/serializers.py`
- Modify: `apps/expenses/api_views.py`
- Modify: `apps/expenses/serializers.py`
- Modify: `apps/accounting/api_views.py`
- Modify: `apps/accounting/serializers.py`
- Modify: `apps/products/api_views.py`
- Modify: `apps/products/serializers.py`
- Modify: `apps/inventory/api_views.py`
- Modify: `apps/inventory/serializers.py`
- Modify: `apps/purchasing/api_views.py`
- Modify: `apps/purchasing/serializers.py`
- Modify: `apps/sales/api_views.py`
- Modify: `apps/sales/serializers.py`
- Modify: `apps/payroll/api_views.py`
- Modify: `apps/payroll/serializers.py`
- Modify: `apps/marketing/api_views.py`
- Modify: `apps/marketing/serializers.py`
- Create: `apps/api/tests/test_domain_isolation.py`

**Interfaces:**
- Consumes: Task 3 tenant viewsets and request-company resolver.
- Produces: tenant-scoped APIs for all registered business routes and tenant-scoped serializer relationship querysets.

- [ ] **Step 1: Write failing two-company API contract tests**

Parameterize representative root and child endpoints from every domain. Assert company A cannot list, retrieve, edit, delete, or link company B records. Explicitly cover a forged centre/client/product/user/campaign/project/document ID and singleton/sequence behavior. Assert superuser filtering and ecosystem access remain available.

- [ ] **Step 2: Run the API contract tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.api.tests.test_domain_isolation -v 2`
Expected: FAIL with cross-company records visible or selectable.

- [ ] **Step 3: Apply tenant viewsets and scoped serializer fields**

Set `company_lookup` for each child endpoint (for example `invoice__company`, `board__company`, or `document__library__company`). Assign direct company fields server-side. In serializer `get_fields()` or `__init__`, scope every user/model choice to the effective company and call `validate_same_company` for compound relationships.

- [ ] **Step 4: Run domain and existing API tests GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.api.tests apps.clients apps.engagements apps.documents apps.tasks apps.billing apps.expenses apps.accounting apps.products apps.inventory apps.purchasing apps.sales apps.payroll apps.marketing -v 1`
Expected: PASS.

- [ ] **Step 5: Commit API isolation**

```bash
git add apps/*/api_views.py apps/*/serializers.py apps/api/tests/test_domain_isolation.py
git commit -m "feat: isolate business APIs by company"
```

### Task 5: Scope HTML workflows, services, dashboards, and AI

**Files:**
- Modify: business app `views.py` and `forms.py` files under `apps/` (excluding the embedded uninstalled project)
- Modify: `apps/core/context_processors.py`
- Modify: service/query/report modules under `functionalities/`
- Create: `apps/companies/tests/test_html_isolation.py`
- Create: `apps/companies/tests/test_service_isolation.py`

**Interfaces:**
- Consumes: Task 1 tenancy helpers.
- Produces: request/company parameters for business service functions and scoped HTML/form behavior.

- [ ] **Step 1: Write failing page and service isolation tests**

Cover CRM dashboard counts, client/engagement pages, finance/accounting reports, inventory workspace, project boards, marketing summaries/calendar/analytics, document searches, notifications, alert generation, and AI pipeline reads with two companies. Assert form choices and direct HTML detail URLs cannot cross tenants.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_html_isolation apps.companies.tests.test_service_isolation -v 2`
Expected: FAIL because global service and page querysets include company B.

- [ ] **Step 3: Thread company scope through HTML and service code**

Resolve the company once at each authenticated request boundary and pass `company` explicitly into services. Require a `company` parameter for scheduled/management service entry points. Replace global `.objects` reads with direct company filters or parent-path filters. Scope form/model-choice fields during form initialization.

- [ ] **Step 4: Verify page and service tests GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_html_isolation apps.companies.tests.test_service_isolation -v 2`
Expected: PASS.

- [ ] **Step 5: Commit non-API isolation**

```bash
git add apps/*/views.py apps/*/forms.py apps/core/context_processors.py functionalities apps/companies/tests/test_html_isolation.py apps/companies/tests/test_service_isolation.py
git commit -m "feat: scope application workflows by company"
```

### Task 6: Secure files, marketing jobs, webhooks, and Academy activity

**Files:**
- Modify: `apps/documents/models.py`
- Modify: `apps/documents/api_views.py`
- Modify: `apps/tasks/models.py`
- Modify: `apps/marketing/models.py`
- Modify: `apps/marketing/api_views.py`
- Modify: `apps/marketing/webhook_views.py`
- Modify: `functionalities/marketing/dispatch.py`
- Modify: `functionalities/marketing/queries.py`
- Modify: `functionalities/marketing/analytics.py`
- Modify: `functionalities/marketing/scheduling.py`
- Modify: `functionalities/marketing/webhooks.py`
- Modify: `apps/academy/api_views.py`
- Modify: `apps/academy/views.py`
- Create: `apps/companies/tests/test_async_and_files.py`
- Create: `apps/academy/tests/test_company_isolation.py`

**Interfaces:**
- Consumes: tenant ownership paths and explicit company service parameters.
- Produces: company-prefixed upload paths; tenant-safe marketing work; Academy user-activity isolation while retaining global catalogue access.

- [ ] **Step 1: Write failing file, marketing, and Academy tests**

Assert uploads for two companies use different company prefixes; scheduled dispatch selects only due messages belonging to the requested company; retry/cancel cannot cross tenants; provider callbacks update only the matched tenant-owned message; Academy users cannot read another company's enrollments, submissions, registrations, bookings, conversations, messages, or private user activity while both can read shared catalogue content.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_async_and_files apps.academy.tests.test_company_isolation -v 2`
Expected: FAIL because paths/jobs/user-activity queries are not tenant-aware.

- [ ] **Step 3: Implement explicit background and storage tenancy**

Include company identity in upload paths. Require `company` for scheduler entry points and derive dispatch ownership from `OutboundMessage.company`. Keep webhook lookup provider-global but bind all mutations to the located message and return no tenant data. Scope Academy activity through user-company relations without adding company fields to shared catalogue models.

- [ ] **Step 4: Verify focused and existing marketing/Academy tests GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_async_and_files apps.marketing apps.academy -v 1`
Expected: PASS.

- [ ] **Step 5: Commit background, file, and Academy isolation**

```bash
git add apps/documents apps/tasks apps/marketing apps/academy functionalities/marketing apps/companies/tests/test_async_and_files.py
git commit -m "feat: isolate files and background workflows"
```

### Task 7: Company administration and ecosystem analytics

**Files:**
- Modify: `apps/companies/admin.py`
- Modify: tenant-owned app `admin.py` files under `apps/`
- Modify: `apps/admin_panel/views.py`
- Modify: `apps/analytics/api_views.py`
- Modify: `apps/analytics/services.py`
- Modify: `apps/api/urls.py`
- Modify: `apps/core/context_processors.py`
- Modify: `templates/base.html`
- Create: `apps/companies/tests/test_admin.py`
- Create: `apps/analytics/tests/test_ecosystem.py`

**Interfaces:**
- Consumes: company ownership and superuser permissions.
- Produces: `ecosystem_overview(company_ids=None) -> dict`; superuser-only `GET /api/v1/analytics/ecosystem/`; current-company navigation context.

- [ ] **Step 1: Write failing admin and ecosystem tests**

Assert normal staff admin querysets/foreign-key choices are tenant-scoped, superusers can administer all companies, non-superuser creation requires a company, tenant dashboards show only current-company metrics, and only superusers can access grouped ecosystem counts/totals across companies.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_admin apps.analytics.tests.test_ecosystem -v 2`
Expected: FAIL because admin scoping and ecosystem analytics do not exist.

- [ ] **Step 3: Implement administration and ecosystem reporting**

Add a reusable tenant admin mixin for non-superuser queryset and foreign-key scoping. Implement grouped, aggregate-only ecosystem results in `ecosystem_overview`; protect the endpoint with `IsAdminUser` plus `is_superuser`; display the current company name in shared navigation without adding a switcher.

- [ ] **Step 4: Verify admin and analytics tests GREEN**

Run: `.venv\Scripts\python.exe manage.py test apps.companies.tests.test_admin apps.analytics.tests.test_ecosystem -v 2`
Expected: PASS.

- [ ] **Step 5: Commit administration and analytics**

```bash
git add apps/*/admin.py apps/admin_panel/views.py apps/analytics apps/api/urls.py apps/core/context_processors.py templates/base.html apps/companies/tests/test_admin.py
git commit -m "feat: add tenant administration and ecosystem analytics"
```

### Task 8: Full migration, regression, and browser verification

**Files:**
- Modify: `.env.example`
- Modify: `docs/release-checklist.md`
- Create: `docs/company-tenancy.md`
- Modify: existing test fixtures only where company assignment is required

**Interfaces:**
- Consumes: all prior tasks.
- Produces: operator documentation and complete verification evidence.

- [ ] **Step 1: Document tenancy operations**

Document default-company migration behavior, company/user creation in Admin, inactive/missing-company behavior, superuser ecosystem access, backup/rollback expectations, and post-migration row-count checks. Add `DEFAULT_COMPANY_NAME=Default Company` only if the implemented migration reads it through a migration-safe mechanism; otherwise document the fixed value and do not add a misleading environment variable.

- [ ] **Step 2: Check migration consistency on a fresh test database**

Run: `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

Run: `.venv\Scripts\python.exe manage.py migrate --plan`
Expected: a valid dependency-ordered plan with no conflicts.

- [ ] **Step 3: Run the complete Django suite**

Run: `.venv\Scripts\python.exe manage.py test -v 1`
Expected: all tests PASS with zero failures/errors.

- [ ] **Step 4: Run browser acceptance suites**

Run the project server and then:

```powershell
.venv\Scripts\python.exe tests\browser\test_crm_navigation.py
.venv\Scripts\python.exe tests\browser\test_inventory_workspace.py
.venv\Scripts\python.exe tests\browser\test_task_workspace.py
.venv\Scripts\python.exe tests\browser\test_marketing_workspace.py
.venv\Scripts\python.exe tests\browser\test_academy_management.py
```

Expected: each script reports PASS; any pre-existing unrelated failure is recorded explicitly rather than hidden.

- [ ] **Step 5: Inspect final scope and commit documentation/fixtures**

Run: `git diff --check`
Expected: no whitespace errors.

Run: `git status --short`
Expected: only intended tenancy changes plus the user's pre-existing unrelated files.

```bash
git add .env.example docs/company-tenancy.md docs/release-checklist.md apps tests
git commit -m "test: verify company tenant isolation"
```
