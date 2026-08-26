# JBS SME Business Suite — Updated Master Plan

**Status:** Approved product direction and implementation roadmap

**Updated:** 26 August 2026

**Current product:** Working JBS Institutional CRM

**Target product:** An integrated, modular SME operating platform for South African small businesses

---

## 1. Product vision

Evolve the existing CRM into a single SME business suite that helps a small business manage customers, operations, money, growth, documents, tasks, and compliance without switching between unrelated tools.

The CRM remains the system's foundation and source of customer and engagement data. New modules must share the same users, permissions, clients, audit trail, notifications, search, visual language, and reporting layer. They must not be built as separate applications with separate logins or duplicate customer records.

The product should progress from:

> CRM → SME Operations Suite → Financial and Compliance Platform → Intelligent Business Assistant

### Product principles

- One login, one sidebar, one business data model.
- Modular: a business can enable only the modules it needs.
- API-first Django architecture with thin views and business logic in `functionalities/`.
- Mobile-friendly and usable by non-technical small-business owners.
- South African defaults: ZAR, VAT, SARS-ready records, POPIA-aware document handling, local addresses and tax identifiers.
- Consistent UJ design system: existing sidebar shell, Bootstrap components, orange accent, dark navigation, typography, forms, tables, cards, toasts, and accessibility conventions.
- PostgreSQL for production; SQLite remains acceptable for local development only.
- Every financial event is traceable to its source document and user.

---

## 2. Current-state audit

### Existing working modules to preserve

| Suite capability | Current implementation | Decision |
|---|---|---|
| Business dashboard | `apps.core` | Extend into a cross-module business dashboard |
| CRM and customers | `apps.clients`, `apps.engagements` | Preserve as the customer master and sales relationship layer |
| People and structure | `apps.staff`, `apps.centres`, `apps.accounts` | Preserve; later extend for employee/payroll profiles |
| Basic finance | `apps.finance.FinancialRecord` | Preserve during transition; evolve through a controlled finance migration |
| Alerts | `apps.alerts` | Preserve and generalise for all suite modules |
| Reports and analytics | `apps.analytics` | Preserve and extend with finance, sales, stock and marketing reporting |
| Communication health | `apps.communication` | Preserve; connect email/marketing and customer support events |
| Administration and roles | `apps.admin_panel`, custom `User` | Preserve and expand to module permissions |
| AI insights | `apps.ai` | Preserve; only use governed, explainable data from enabled modules |
| REST API | `apps.api` and DRF | Preserve and version before public integrations |

### Database audit (26 August 2026)

- Active database: SQLite (`db.sqlite3`), 19 tables.
- Django system check: no issues.
- Current domain models: `User`, `StaffProfile`, `Centre`, `Client`, `Engagement`, `FinancialRecord`, `Alert`, and `CommunicationLog`.
- The database does **not** yet contain document management, Kanban tasks, invoices, payments, expenses, chart of accounts, journals, inventory, purchasing, sales orders, e-commerce, marketing, payroll, tax, support, workflow, or integration entities.
- Existing `FinancialRecord` tracks revenue, pipeline, and expenses against engagements. It is useful for CRM reporting but is not a double-entry accounting ledger and must not be presented as full bookkeeping.

### ProjectManagementAPP_FinalBoss decision

`ProjectManagementAPP_FinalBoss` is a separate, older Django project with its own settings, users, models, templates, static files, migrations, and project-management concepts. A second copy also exists under `apps/ProjectManagementAPP_FinalBoss/`. Directly mounting either project would create duplicate authentication, inconsistent styling, migration risk, and conflicting business concepts.

Decision:

1. Do not integrate it as a runtime application.
2. Build a small native `apps.tasks` Kanban module in the main CRM database.
3. Reuse only proven concepts where useful: board states, assignment, due dates, comments, attachments, and activity history. Do not copy its user system or unrelated academic/project features.
4. Keep both legacy folders read-only during the migration audit.
5. After the new Kanban is accepted and any required data is migrated, archive the legacy project outside the production application. Deletion requires an explicit backup and approval.

---

## 3. Target module catalogue

The sidebar and app launcher will follow the four groups in the supplied SME module reference. Existing capabilities are reused instead of duplicated.

### A. Finance & Accounting

#### 1. Invoicing & Billing — new, Priority 1

Create quotes, recurring or once-off invoices, credit notes, customer statements, payment receipts, reminders, and PDF/email delivery.

Core entities: `Quote`, `QuoteLine`, `Invoice`, `InvoiceLine`, `CreditNote`, `Payment`, `PaymentAllocation`, `BillingProfile`, `NumberSequence`.

Integration:

- Customer comes from CRM `Client`.
- An accepted quote may create/update an `Engagement` and optionally a `SalesOrder`.
- Posted invoices create accounting journal entries; payment allocations update receivables.
- Documents are stored in Document Management, not as disconnected file paths.
- Defaults: ZAR, South African date/address formats, configurable VAT rate, tax invoice fields, company registration and VAT numbers.

#### 2. Expense Tracking — new, Priority 1

Capture supplier expenses, receipts, mileage, categories, payment method, VAT portions, approval status, cost centre, client/engagement, and reimbursable status.

Core entities: `Expense`, `ExpenseCategory`, `ExpenseReceipt`, `MileageClaim`, `ExpenseApproval`.

Integration: receipt files use Document Management; approved expenses post to bookkeeping; engagement-linked expenses contribute to profitability.

#### 3. Accounting & Bookkeeping — new, Priority 2

Provide a proper double-entry ledger, chart of accounts, journals, bank/cash accounts, customer and supplier balances, trial balance, profit and loss, balance sheet, cash-flow view, and period closing.

Core entities: `Account`, `JournalEntry`, `JournalLine`, `AccountingPeriod`, `BankAccount`, `BankTransaction`, `Reconciliation`, `TaxCode`.

Rules:

- Every posted journal must balance debits and credits.
- Posted entries are immutable; corrections use reversal entries.
- Invoice, payment, expense, payroll, stock, and tax modules post through accounting services, never by writing journal rows in views.
- Existing `FinancialRecord` remains a CRM metric during migration; ledger-derived reporting becomes the authoritative finance source after reconciliation.

#### 4. Payroll Management — planned, Priority 3

Employee payroll profiles, earnings, deductions, benefits, leave inputs, payslips, payroll runs, payment files, and accounting postings.

South African scope: PAYE, UIF, SDL, tax-year configuration and exportable reconciliation data. Statutory calculations must be versioned by effective date and verified against current SARS rules before production release.

#### 5. Tax & Compliance — planned, Priority 3

VAT periods and reports, tax-code mapping, provisional tax support, payroll compliance outputs, compliance calendar, filing reminders, evidence packs, and audit exports.

This module assists record preparation; it must clearly avoid claiming that a draft calculation has been filed with SARS. Filing integrations require explicit supported providers and audit receipts.

### B. Operations & Management

#### 6. Inventory Management — new, Priority 2

Products, variants, units, warehouses/locations, stock movements, stock counts, reorder levels, reservations, valuation, batches/serials where enabled, and low-stock alerts.

Core entities: `Product`, `ProductVariant`, `Location`, `StockMovement`, `StockLevel`, `StockCount`, `ReorderRule`.

#### 7. Purchase Management — new, Priority 2

Supplier register, purchase requisitions, purchase orders, goods receipts, supplier bills, returns, and approval flow.

Core entities: `Supplier`, `PurchaseOrder`, `PurchaseOrderLine`, `GoodsReceipt`, `SupplierBill`.

Integration: receipts increase stock; supplier bills post payables; supplier documents use Document Management.

#### 8. Sales Orders — new, Priority 2

Convert accepted quotes into sales orders, manage fulfilment, delivery notes, backorders, returns, and invoicing.

Core entities: `SalesOrder`, `SalesOrderLine`, `Fulfilment`, `DeliveryNote`, `Return`.

#### 9. CRM & Customers — existing

Keep clients, relationship owners, engagements, contact history, stages, health scoring, visibility, and centre ownership. Extend carefully with contact persons, billing/shipping addresses, consent/preferences, customer tags, and a single customer timeline containing sales, invoice, support, marketing, task, and document events.

#### 10. Projects & Tasks — replace legacy app, Priority 1

Create a lightweight persistent Kanban in `apps.tasks`.

MVP capabilities:

- Boards and configurable columns (`Backlog`, `To Do`, `In Progress`, `Blocked`, `Done`).
- Task cards with title, description, priority, assignee, creator, due date, labels, checklist, and sort order.
- Link tasks to a client, engagement, invoice, document, or other supported business record through controlled references.
- Drag-and-drop status/order updates saved to the database through a transactional service/API.
- Comments, attachments via Document Management, watchers, reminders, and an append-only activity history.
- List/My Tasks view and overdue task alerts.
- Permission scopes: private, team/centre, and organisation.

Out of MVP scope: Gantt charts, complex resource planning, academic papers, conferences, learning content, student/supervisor workflows, and a separate project authentication system.

### C. Growth & Marketing

#### 11. Marketing Tools — new, Priority 2

Audience segments, email/SMS campaign drafts, templates, scheduling, consent enforcement, delivery events, unsubscribes, lead source tracking, and campaign performance.

Core entities: `Campaign`, `Segment`, `MessageTemplate`, `CampaignRecipient`, `DeliveryEvent`, `ConsentRecord`.

POPIA rule: marketing sends require a recorded lawful basis/consent configuration, suppression lists, and auditable opt-out handling.

#### 12. Social Media Manager — planned, Priority 4

Content calendar, post drafts, approvals, scheduled publishing, channel connections, and performance snapshots. Provider tokens must be encrypted and isolated in the Integrations module.

#### 13. Website & Landing Pages — pending, Priority 4

This is the requested site builder. Keep it explicitly pending until core commerce, finance, permissions, document storage, and deployment isolation are stable.

Proposed first release: theme-based landing pages, reusable sections, forms connected to CRM leads, custom domains, SEO metadata, preview/publish workflow, and version history. Do not begin with an unrestricted page builder or arbitrary server-side code execution.

#### 14. E-commerce — new, Priority 3

Storefront catalogue, pricing, cart, checkout, orders, payment status, shipping/collection, refunds, customer account, and stock synchronisation.

Core entities: `Store`, `Catalogue`, `Cart`, `CartItem`, `WebOrder`, `WebOrderLine`, `CheckoutSession`, `Refund`.

Integration: uses Inventory products, CRM customers, Sales Orders, Invoice/Billing, payment gateway adapters, accounting postings, and Document Management for generated records. Card details must never be stored in this application.

#### 15. Customer Support — new, Priority 3

Shared support inbox, ticket number, customer/requester, category, priority, SLA, assignee, status, comments, attachments, canned responses, and knowledge base.

Tickets appear in the unified CRM customer timeline and may create Kanban tasks.

### D. Insights & Control

#### 16. Business Dashboard — existing, extend continuously

Provide role-aware, cross-module KPIs: cash position, overdue invoices, revenue, expenses, profit, pipeline, sales, stock risk, tasks, support SLAs, campaign performance, and compliance deadlines. Every KPI links to its underlying records.

#### 17. Reports & Analytics — existing, extend continuously

Add receivables ageing, sales by customer/product, expense breakdown, P&L, balance sheet, cash flow, VAT report, stock movement/valuation, campaign funnel, task throughput, and support SLA reports. Include CSV/PDF export and saved filters with permission-aware data.

#### 18. Document Management — new, Priority 1

Build a SharePoint-inspired document workspace, adapted to SME needs and the existing UJ styling.

MVP interface:

- Left navigation for `My Files`, `Shared`, `Recent`, `Favourites`, and `Trash`.
- Main library view with breadcrumbs, folder navigation, list/grid toggle, search, filters, sort, upload, new folder, and metadata columns.
- Details panel with preview/download, owner, size/type, version, tags, related client/engagement, sharing information, and activity.
- Drag-and-drop upload with progress and clear validation errors.
- Responsive layout and the existing base shell/sidebar, buttons, tables, cards, toasts, focus states, and colour tokens.

Core entities:

- `DocumentLibrary`: organisation/team/personal library and permission boundary.
- `Folder`: hierarchical folders with protected move/delete rules.
- `Document`: stable logical record, title, owner, classification, tags, related business object, and current version.
- `DocumentVersion`: immutable file version, storage key, original name, MIME type, size, checksum, uploader, and timestamp.
- `DocumentPermission`: user/team access (`view`, `edit`, `manage`, `share`).
- `DocumentShare`: internal share or expiring public link, disabled by default for sensitive classes.
- `DocumentActivity`: upload, view, download, rename, move, share, restore, and delete audit events.
- `DocumentFavourite` and `DocumentTag`.

Security and storage rules:

- Store file metadata in PostgreSQL and file bytes in private object storage; local media storage is development-only.
- Never trust file extensions. Validate size, MIME signature, permitted types, and filename; add malware scanning before production.
- Authorise every list, preview, download, update, and share request at object level.
- Use time-limited signed download links; do not expose raw storage paths.
- Soft-delete to Trash with retention, restore, then authorised purge.
- Version rather than overwrite; retain checksums and audit events.
- Classifications: `Public`, `Internal`, `Confidential`, `Restricted` with sharing rules.
- POPIA support: least privilege, access logs, retention policy, subject-data search/export workflow, and breach/audit evidence. Final policies require legal review.

Integrations:

- Attach documents to clients, engagements, tasks, invoices, expenses, suppliers, products, marketing campaigns, and support tickets.
- Generated invoices, statements, receipts, purchase orders, delivery notes, payslips, and reports are registered as documents.
- Document events can trigger notifications and workflows.

#### 19. Automation & Workflows — planned, Priority 3

Event/condition/action automation with templates, approvals, scheduled jobs, retries, execution logs, and a kill switch.

Example workflows: invoice overdue → reminder + task; expense over threshold → manager approval; stock below reorder level → draft purchase order; new website lead → CRM client/lead + follow-up task.

#### 20. Integrations — foundation in Priority 2, connectors added incrementally

Provide a controlled adapter layer for banks, payment gateways, email/SMS, cloud storage, social providers, shipping, and accounting/tax services.

Core entities: `IntegrationConnection`, `CredentialReference`, `WebhookEndpoint`, `WebhookEvent`, `SyncRun`, `ExternalMapping`.

Rules: encrypt secrets outside normal model fields, verify webhook signatures, use idempotency keys, log sync outcomes without sensitive payloads, and allow administrators to disconnect/revoke providers.

---

## 4. Navigation and information architecture

The permanent sidebar should remain compact. Use collapsible groups and show only modules the current user may access.

```text
Overview
  Dashboard

Sales & Customers
  CRM & Customers
  Engagements
  Sales Orders
  Customer Support

Finance & Accounting
  Invoicing & Billing
  Expenses
  Accounting & Bookkeeping
  Payroll
  Tax & Compliance

Operations
  Inventory
  Purchases
  Tasks & Kanban
  Documents

Growth & Commerce
  Marketing
  Social Media
  E-commerce
  Website Builder (Pending)

Insights & Control
  Reports & Analytics
  Alerts
  Automation
  Integrations

Administration
  Staff & Teams
  Organisation Settings
  Users & Permissions
```

Navigation rules:

- Keep Dashboard first and Administration last.
- Use route-aware active states and remember collapsed groups.
- Add a module launcher and global search rather than letting the sidebar grow indefinitely.
- On mobile, use the existing off-canvas pattern.
- Feature flags hide incomplete modules; do not ship dead links.
- Preserve existing CRM URLs where possible to avoid breaking bookmarks.

---

## 5. Shared platform architecture

### Recommended Django apps

```text
Existing
  accounts, core, admin_panel, staff, centres, clients, engagements,
  finance, alerts, analytics, communication, ai, api

Priority 1
  documents, tasks, billing, expenses

Priority 2
  accounting, products, inventory, purchasing, sales,
  marketing, integrations

Priority 3
  commerce, payroll, compliance, support, workflows

Priority 4
  social, sites
```

Each new domain follows the existing convention:

```text
apps/<domain>/
  models.py, forms.py, views.py, urls.py, api_views.py,
  serializers.py, permissions.py, admin.py, tests/, migrations/

functionalities/<domain>/
  services.py, validators.py, handlers.py

templates/<domain>/
static/ (shared theme; domain-specific JS only where required)
```

### Shared entities to introduce before module sprawl

- `Organisation`: tenant/business identity, locale, currency, registration and tax settings.
- `Team` / organisation membership: do not rely only on global Django `is_staff`.
- Module entitlements and role permissions.
- `Address`, `ContactPerson`, `Money`/currency conventions, and number sequences.
- `AuditEvent`: actor, action, target, timestamp, request/source and safe change summary.
- `Notification`: reusable in-app/email/SMS notification state.
- Tags, notes, comments, attachments and activity timeline primitives.
- Feature flags and organisation settings.

### Multi-tenancy direction

Before offering the system to unrelated businesses, add an `Organisation` ownership boundary to every business record and enforce it in query services, forms, APIs, jobs, exports, and object permissions. Use shared-schema tenancy initially, with database constraints and automated cross-tenant access tests. The current single-institution data must be migrated into the first organisation.

### API direction

- Introduce `/api/v1/` while preserving current endpoints through a deprecation period.
- Use consistent pagination, filtering, error payloads and idempotency for financial/commerce writes.
- Require object-level permissions and organisation scoping in every viewset.
- Publish webhook events through an outbox pattern after database commit.

---

## 6. Critical cross-module workflows

### Quote to cash

```text
CRM Client → Quote → Acceptance → Sales Order/Fulfilment → Invoice
→ Payment → Bank Reconciliation → Accounting Journal → Dashboard/Reports
```

### Procure to pay

```text
Supplier → Purchase Order → Goods Receipt → Stock Increase
→ Supplier Bill/Expense → Approval → Payment → Accounting Journal
```

### Document collaboration

```text
Upload → Validate/Scan → Create Immutable Version → Apply Permissions
→ Link to Business Record → Notify Collaborators → Audit Every Action
```

### Lead to customer

```text
Website/Marketing Lead → Consent and Source → CRM Record
→ Follow-up Kanban Task → Engagement/Quote → Customer Timeline
```

### E-commerce order

```text
Catalogue → Cart → Hosted Payment → Webhook Verification → Sales Order
→ Reserve/Reduce Stock → Invoice/Receipt → CRM Timeline → Accounting
```

---

## 7. Security, governance and South African readiness

- Enforce organisation and object-level access on HTML views, APIs, files, exports, background jobs, and search.
- Apply least privilege, MFA-ready authentication, secure sessions, rate limits, CSRF protection, and auditable administration.
- Encrypt secrets and sensitive data appropriately; keep credentials out of source code and database logs.
- Maintain append-only audit history for financial posting, permissions, sharing, exports and compliance actions.
- POPIA: purpose limitation, consent/lawful-basis records, data minimisation, retention, access/correction/export workflows, processor register, and incident evidence.
- Financial controls: sequential document numbers, period locks, approval thresholds, reversals, reconciliations, and segregation of duties.
- Payment controls: use hosted/tokenised gateways; never store CVV or raw card data.
- Backup policy: encrypted automated backups, restore tests, retention schedule, and recovery objectives.
- Accessibility: retain WCAG 2.1 AA patterns and keyboard-accessible Kanban alternatives.
- SARS, CIPC, payroll and banking rules change. Version statutory configuration by effective date and verify it against current official guidance before each production release.

---

## 8. Delivery roadmap

### Phase 0 — Platform hardening and design (2–3 weeks)

- Create Architecture Decision Records for tenancy, storage, accounting and legacy project retirement.
- Add `Organisation`, membership, module permissions, audit events and feature flags.
- Establish PostgreSQL migration plan, private object-storage strategy and test environments.
- Produce UI wireframes for the grouped sidebar, document library and Kanban.
- Inventory/backup both legacy `ProjectManagementAPP_FinalBoss` directories; identify any data that must be migrated.
- Add CI checks for migrations, tests, linting, security and cross-tenant isolation.

**Exit:** existing CRM passes regression tests inside the organisation boundary and no current URL/data is lost.

### Phase 1 — SME essentials (6–8 weeks)

1. Document Management MVP.
2. Native Tasks & Kanban MVP with persistent storage.
3. Invoicing & Billing MVP.
4. Expense Tracking MVP.
5. Updated grouped/sidebar navigation and module launcher.
6. Cross-module activity timeline, alerts and dashboard widgets.

**Exit:** a business can manage customers, files, tasks, quotes/invoices, payments and expenses in one application with audit history.

### Phase 2 — Operations and bookkeeping (8–12 weeks)

1. Double-entry accounting, chart of accounts and financial statements.
2. Product catalogue and Inventory.
3. Purchase Management.
4. Sales Orders and fulfilment.
5. Marketing campaigns and consent/suppression handling.
6. Integration framework plus first payment, messaging and banking adapters.
7. Reconcile and migrate authoritative data from `FinancialRecord`.

**Exit:** quote-to-cash and procure-to-pay work end-to-end and reconcile to the ledger.

### Phase 3 — Growth, service and compliance (8–12 weeks)

1. E-commerce storefront and payment workflow.
2. Customer Support and knowledge base.
3. Automation & Workflows.
4. Payroll Management.
5. Tax & Compliance workspace.
6. Expanded reports, exports and executive insights.

**Exit:** operational, payroll, tax-support and commerce workflows use the shared accounting and audit foundation.

### Phase 4 — Expansion (after core stability)

1. Social Media Manager.
2. Website & Landing Page Builder.
3. Advanced integrations and partner marketplace.
4. Governed AI assistance: document extraction, cash-flow warnings, collections suggestions and natural-language reporting with human approval.

**Exit:** optional growth tools are production-isolated, observable and do not weaken core-suite security.

---

## 9. Testing and acceptance strategy

Every module requires:

- Model constraints and migration tests.
- Service/validator unit tests; no business rules hidden in views.
- Permission and organisation-isolation tests for every CRUD action and download/export.
- API tests, including duplicate submissions and idempotency for payments/posting.
- Workflow integration tests across module boundaries.
- Browser tests for key paths and responsive/accessibility checks.
- Audit-event assertions for sensitive actions.
- Backup/restore and failed-job recovery exercises before production.

Priority 1 acceptance journeys:

1. Upload, version, share, revoke, restore and securely download a document.
2. Create a Kanban task, assign it, drag it between columns, reload, and retain state/history.
3. Create a CRM quote, convert it to an invoice, record a partial/full payment, and produce a statement.
4. Capture an expense receipt, approve it, link it to an engagement, and include it in profitability reporting.
5. Prove a user from one organisation cannot see another organisation's records, files, search results, IDs or exports.

---

## 10. Definition of done

A module is complete only when:

- It is integrated into shared authentication, organisation scoping, roles, sidebar, search, notifications, audit, documents and reporting where applicable.
- Its data model and cross-module contracts are documented and migrated safely.
- All material business logic lives in `functionalities/<domain>/`.
- HTML and `/api/v1/` endpoints enforce the same permissions.
- Empty, loading, validation, error and permission-denied states are designed.
- Automated tests pass and the principal browser journey has been verified.
- Operational documentation covers configuration, backup, monitoring and rollback.
- Feature flags permit safe rollout and rollback.
- No unfinished sidebar links are exposed to users.

---

## 11. Immediate implementation backlog

The next execution cycle should implement these items in order:

1. ADRs and schema design for `Organisation`, permissions, audit, file storage and accounting boundaries.
2. Grouped sidebar/module registry behind feature flags, with existing routes unchanged.
3. `apps.documents` MVP plus secure download service and object permissions.
4. `apps.tasks` persistent Kanban, deliberately independent of the legacy project app.
5. `apps.billing` quotes, invoices, payments and document generation.
6. `apps.expenses` receipts and approval flow.
7. Cross-module dashboard widgets and customer activity timeline.
8. PostgreSQL staging migration and production-readiness validation.

No legacy folder should be deleted, no financial source of truth should be switched, and no compliance calculation should be released until its migration/reconciliation and acceptance gates have passed.

### Implementation progress — 26 August 2026

- Completed: Document Management, Tasks & Kanban, Invoicing & Billing, and Expense Tracking backend/API foundations and initial API-driven screens.
- Completed: Phase 2 backend foundations for chart of accounts/journals, products, stock movements, purchasing, sales orders, goods receipts, fulfilment, and sales-order-to-invoice conversion.
- Completed: Phase 2 API-driven screens for products/services, inventory, purchasing, sales orders, and accounting.
- Completed: Phase 2 workflow completion for partial goods receipts and fulfilments, supplier bills, accounting reversals, and automatic invoice, payment, expense and supplier-bill ledger postings using configured system accounts.
- Completed: Phase 2 financial controls for API-driven trial balance, income statement, balance sheet, bank-statement import, exact ledger matching, reconciliation and reversal of matches.
- Next: Purchase and sales returns, marketing, integration adapters, organisation isolation, report exports, and authoritative `FinancialRecord` reconciliation.

---

## 12. Success measures

- A new SME user can reach any daily function in no more than three navigation actions.
- At least 90% of invoices, expenses, documents and tasks are linked to the correct customer, engagement or business record.
- Zero cross-organisation data leaks in automated isolation tests.
- All posted journal entries balance and every posting traces to a source event/document.
- Document permission changes and downloads are fully auditable.
- Kanban state persists reliably across reloads and concurrent updates.
- Overdue invoices, low stock, overdue tasks and compliance dates surface on the dashboard before they become business failures.
- Existing CRM regression journeys remain intact throughout the expansion.

---

*This plan supersedes the earlier CRM-only master prompt. The existing CRM is the base product; the listed modules extend it into a cohesive SME suite rather than replacing it.*
