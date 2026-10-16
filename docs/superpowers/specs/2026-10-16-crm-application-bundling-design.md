# CRM Application Bundling Design

**Date:** 16 October 2026  
**Status:** Approved in-chat design awaiting written review  
**Related provider design:** `docs/superpowers/specs/2026-09-28-marketing-communications-integration-design.md`

## 1. Objective

Make Academy's Business Tools page a small application launcher rather than a catalogue of every route. It must show exactly six applications, in this order:

1. Invoicing
2. Inventory
3. Project Management
4. Marketing
5. CRM
6. Documents

Every other authenticated business tool is discoverable through CRM, using a persistent CRM sidebar that extends the visual and interaction pattern of the existing Project Management sidebar. Existing application URLs, data models, permissions, and bookmarks remain valid.

The same release verifies the already implemented official Twilio and Meta Marketing providers, applies the pending Marketing migration that causes the local Marketing workspace failure, and stops after automated and browser-level regression testing.

## 2. Scope boundaries

This work reorganizes application discovery and navigation. It does not merge databases, move Django models between applications, rewrite existing tools as a single-page application, or replace their canonical URLs.

The existing Marketing provider implementation remains the source of truth. No second provider framework will be introduced. Provider secrets remain environment-only, and an unconfigured provider must never stop Django or the non-delivery areas of Marketing from loading.

The current uncommitted Academy template and test changes are user-owned work. Implementation must edit around them and must not discard or replace them.

## 3. Canonical navigation registry

`functionalities/crm_core/navigation.py` remains the server-owned source of labels, icons, URLs, descriptions, and role rules. It will expose separate projections for top-level applications and CRM-contained tools so templates cannot independently drift.

### 3.1 Academy primary applications

Academy receives exactly these entries:

| Position | Label | Canonical route |
|---:|---|---|
| 1 | Invoicing | `/billing/` |
| 2 | Inventory | `/inventory/` |
| 3 | Project Management | `/tasks/` |
| 4 | Marketing | `/growth/` |
| 5 | CRM | `/clients/` |
| 6 | Documents | `/documents/` |

All six use their existing canonical Django URL names rather than literal hostnames. The Academy page must render them in this order for every authenticated role. Authorization inside each destination remains responsible for limiting privileged operations.

No secondary tool, Academy self-link, Business Diagnostic link, or API Explorer link appears as an Academy Business Tools card.

### 3.2 CRM-contained navigation

The CRM sidebar contains the current CRM landing/customer area plus all tools omitted from the six-card Academy launcher. It groups links to keep a long navigation usable:

- **Customers & Revenue:** Customers, Engagements, Sales Orders.
- **Finance:** Expense Tracking, Financial Overview, Accounting, Business Activity.
- **Operations:** Products & Services, Purchasing.
- **Insights:** Reports & Analytics, Alerts, Communication Health, AI Insights.
- **People & Administration:** Staff, Departments, Payroll Management, System Admin.
- **Learning & Developer:** SME Academy, Business Diagnostic, API Explorer.

The CRM item itself opens Customers at `/clients/`; the Customers entry is active there. Payroll is included only for the roles that currently receive Payroll access. System Admin is included only for superusers, staff administrators, Deans, and administrators according to the existing rule. No navigation change grants access to an endpoint that the user could not already use.

## 4. CRM shell and presentation

Authenticated templates for CRM-contained tools continue extending `templates/base.html`. The base shell gains a CRM sidebar partial and CRM-specific stylesheet derived from the Project Management sidebar's structure, spacing, collapse control, icons, active-state treatment, mobile drawer behavior, Business Tools return link, and sign-out placement.

A context processor determines whether the current resolved namespace belongs to the CRM bundle. CRM-contained namespaces render the sidebar and CRM shell classes. Standalone application namespaces do not:

- Billing / Invoicing
- Inventory
- Tasks / Project Management
- Marketing
- Documents
- Academy

Inventory, Tasks, Marketing, and Academy already own standalone shells and remain unchanged except for their return links where needed. Billing and Documents continue using the shared base template but render without the CRM sidebar. Account pages and unauthenticated pages also render without it.

The CRM sidebar highlights the current namespace, supports keyboard focus, exposes accurate `aria-expanded` state, closes on mobile after navigation, and keeps the main content reachable through the existing skip link. The desktop sidebar may collapse to its icon rail in the same manner as Project Management.

## 5. Marketing providers and `/growth/` failure

The repository already implements adapters and tests for:

- Twilio Email API
- Twilio Programmable Messaging for SMS
- Meta WhatsApp Cloud API
- Facebook Page publishing
- Instagram Professional account publishing

The implementation uses environment-backed settings in `jbs_crm/settings/base.py`, documented placeholders in `.env.example`, and setup guidance in `docs/marketing-provider-setup.md`. These remain authoritative and must be checked against the official documentation already cited in those files.

The local database currently has `marketing.0001_initial` unapplied and contains no `marketing_*` tables. The Django shell route renders in an isolated migrated test database, but Marketing API calls fail against the local database. The release fix is to apply the committed Marketing migration to the local development database, then verify both `/growth/` and `/api/v1/marketing/workspace/` resources. No schema redesign is required for this failure.

If provider credentials are absent, `/growth/` must still load and show each provider as not configured. Tests must not make live provider calls.

## 6. Data flow

1. `get_academy_primary_tools(user)` produces the ordered six-card launcher data.
2. `apps.academy.views.academy_index` serializes that list through the existing `academy-tools-data` contract.
3. `get_crm_navigation(user)` produces grouped, role-aware secondary links.
4. The suite context processor exposes CRM navigation plus a flag based on the current resolved namespace.
5. `templates/base.html` includes the CRM sidebar only when that flag is true.
6. Each sidebar link opens its existing Django view; no iframe, local-storage router, or duplicate API layer is added.
7. Marketing's JavaScript continues loading its existing `/api/v1/marketing/` resources after the committed database migration has been applied.

## 7. Error handling

- Reverse URL failures must be caught by tests at registry construction time rather than replaced with hard-coded host URLs.
- An empty or unauthorized CRM navigation group is omitted; it is not rendered as a blank heading.
- The CRM shell must not mask existing Django permission responses.
- Marketing provider status exposes missing variable names and safe guidance only, never secret values.
- Missing Marketing credentials produce disabled delivery controls, not HTTP 500 responses.
- Migration verification must distinguish an unapplied schema from a provider/network failure.

## 8. Testing and acceptance criteria

Implementation follows test-driven development.

### 8.1 Navigation tests

- Academy returns exactly six tool records with the exact order and routes defined in section 3.1.
- None of the secondary routes appear in the Academy tool JSON.
- Every prior non-primary tool appears in the CRM navigation registry.
- Staff users do not receive Payroll or System Admin links.
- Authorized administrative users receive the privileged links allowed by the existing rules.
- CRM-contained pages render the CRM sidebar, active link, Business Tools return link, and sign-out action.
- Billing and Documents do not render the CRM sidebar.
- Existing canonical routes still return their expected authenticated status.

### 8.2 Marketing tests

- The committed Marketing test suite passes without network access or real credentials.
- Provider status returns independent states for email, SMS, WhatsApp, Facebook, and Instagram without leaking configured secrets.
- Twilio Email retains asynchronous `202 Accepted` semantics rather than claiming delivery.
- SMS sender-number versus Messaging Service behavior remains covered.
- Meta endpoints remain versioned and publishing flow tests remain mocked.
- A migrated local database contains the Marketing tables and `/growth/` no longer fails while loading its API data.

### 8.3 Regression and browser checks

- Run the complete Django test suite and report every unrelated pre-existing failure by name.
- Run the existing Academy, Marketing, Inventory, and Project Management browser tests where their configured browser environment is available.
- Add or update a browser test that confirms the Academy card order and CRM sidebar navigation.
- Load Academy, each of the six applications, and representative CRM-contained pages without console errors attributable to this change.
- Stop after the implementation and verification results are reported; do not begin another restructuring phase.

## 9. Documentation and deployment

`.env.example` continues to list all supported provider variables with empty safe defaults and official setup links. `docs/marketing-provider-setup.md` remains the operator guide and is updated only if verification identifies a real discrepancy.

Deployment notes must explicitly include:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

The migration is run before validating Marketing API endpoints. Credentials are supplied through the deployment environment and are never committed.

## 10. Non-goals

- Combining all Django applications into one physical Django app.
- Changing existing business records or importing sample Marketing metrics.
- Rebuilding the secondary tools as CRM tabs or embedding them in iframes.
- Renaming or removing canonical routes.
- Adding new communication providers beyond the five already requested.
- Sending live email, SMS, WhatsApp, Facebook, or Instagram content during tests.
