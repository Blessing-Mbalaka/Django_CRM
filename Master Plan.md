# SME Shell and CRM Integration — Master Plan

**Status:** Approved integration direction

**Updated:** 18 September 2026

**Source prototype:** `SMEs (3)/SMEs/`

**Host application:** Django CRM in this repository

**Primary decision:** The SME experience becomes the main user-facing shell. Its current CSS and page-specific JavaScript are preserved while pages are brought under Django one at a time. Existing CRM tools remain operational at their current routes and are linked from the SME Tools page; restyling those tools is a later project. Marketing is deliberately implemented last because it requires the largest new schema and API surface.

---

## 1. Goal

Turn the supplied SME front-end prototypes into authenticated Django pages backed by the existing CRM database and `/api/v1/` API. Preserve the current prototype presentation while replacing temporary browser-only state with durable, permission-aware data.

The completed first programme must provide:

- an SME-branded Django home page at the application root;
- Academy, Knowledge Hub, Inventory, and Tasks pages served by Django;
- a Business Tools section linking to the existing CRM applications;
- one authenticated user and profile across the SME shell and CRM tools;
- API-driven user activity and operational records;
- safe additive database migrations where existing tables need more fields;
- automated model, API, route, permission, and integration tests;
- Marketing preserved as a prototype until the final delivery phase.

## 2. Decisions and boundaries

### 2.1 Approved decisions

1. The SME interface, not the current CRM dashboard, becomes the default landing experience.
2. Do not use iframes.
3. Do not rewrite the prototype into a new SPA.
4. Convert each prototype entry point into a Django template while preserving its CSS and visual behaviour.
5. Keep each module in its own template/static folder for maintainability.
6. Use named Django routes in place of relative `.html` links.
7. Use the existing CRM model and API whenever it already represents the same business concept.
8. Add nullable fields or new related models through additive migrations; avoid destructive schema replacement.
9. Curated learning content may remain version-controlled initially. User-generated and operational records must use the database.
10. Existing CRM pages keep their current styling until a separate visual-unification phase.
11. Marketing is the final module in this programme.

### 2.2 Out of scope for the initial integration

- Restyling every existing CRM page to match the SME shell.
- A React, Vue, or other SPA rewrite.
- Multi-tenant organisation isolation unless separately approved.
- Real email/SMS delivery, social publishing, payment processing, or external booking providers.
- Treating sample funding opportunities, mentors, events, certificates, or analytics as live data.
- Implementing Marketing before the rest of the shell and tool integrations are stable.

## 3. Current-state findings

### 3.1 SME prototype

The imported source currently contains five page groups:

| Prototype | Entry point | Current persistence | Main responsibility |
|---|---|---|---|
| Academy | `SMEs (3)/SMEs/academy/index.html` | In-memory JavaScript | Learning paths, courses, diagnostic, tools, mentoring, community, events, profile, settings |
| Knowledge Hub | `SMEs (3)/SMEs/knowledge-hub/index.html` | In-memory JavaScript | Guides, courses, videos, resources, bookmarks, quizzes, compliance and funding education |
| Inventory | `SMEs (3)/SMEs/inventory/index.html` | `localStorage` | Products, categories, suppliers, movements, settings and reports |
| Tasks | `SMEs (3)/SMEs/tasks/index.html` | In-memory JavaScript | Projects, tasks, board, calendar and personal work views |
| Marketing | `SMEs (3)/SMEs/marketing-app/index.html` | In-memory JavaScript | Campaigns, adverts, content, email drafts, leads, brand kit, calendar and analytics |

There is no usable `SMEs (3)/SMEs/index.html` or `invoicing.html` in the imported source, although several relative links expect them. Django routes must replace these broken assumptions.

### 3.2 Meaning of `data.js`

The prototype `data.js` files are not API clients. They currently provide:

- seeded sample/catalogue content;
- initial page state;
- arrays and objects later mutated by `app.js`;
- helper functions that calculate progress and summary values.

The integration must split these responsibilities:

| Concern | Destination |
|---|---|
| Curated course/article/glossary copy | Version-controlled fixtures or static catalogue modules initially |
| Authenticated user data | Django models and `/api/v1/` |
| Temporary UI state | Browser-side `store.js` |
| HTTP, CSRF, pagination, errors | Per-module `api.js` using a shared API client |
| Rendering | Existing `views.js`/`ui.js`, changed only where data shape requires it |
| Event orchestration | Existing `app.js`, calling repositories instead of mutating durable data directly |

### 3.3 Existing CRM capabilities to reuse

The CRM already has working Django apps, routes, models, serializers, APIs, and initial API-driven screens for accounts/profiles, clients, engagements, documents, tasks/projects, products, inventory, purchasing, billing, sales, expenses, accounting, payroll, analytics, alerts, communication, and AI insights.

Both `/api/` and `/api/v1/` currently include the same DRF router. New SME code must use `/api/v1/` only.

## 4. Target structure

Use module folders and preserve ownership of styles and scripts:

```text
apps/
  core/                       SME home route and shell orchestration
  accounts/                   existing authentication and User model
  academy/                    new Academy persistence and API
  knowledge_hub/              new learning-resource persistence and API
  products/                   existing catalogue authority
  inventory/                  existing stock authority
  purchasing/                 existing supplier authority
  tasks/                      existing task/project authority
  marketing/                  new; final phase only

functionalities/
  academy/                    progress, diagnostic, completion services
  knowledge_hub/              bookmark and completion services
  inventory/                  existing domain services
  tasks/                      existing domain services
  marketing/                  final phase only

templates/
  sme/
    home/index.html
    academy/index.html
    knowledge_hub/index.html
    inventory/index.html
    tasks/index.html
    shared/

static/
  sme/
    shared/
      css/
      js/api-client.js
      images/
    home/
    academy/
      css/
      js/data.js
      js/store.js
      js/api.js
      js/ui.js
      js/views.js
      js/app.js
    knowledge-hub/
    inventory/
    tasks/
    marketing/                 retained until final phase
```

Do not duplicate files that are truly shared. Move the existing Inventory design-system CSS to `static/sme/shared/` only after all importing pages are updated in the same change.

## 5. Route and navigation contract

### 5.1 SME shell routes

| Route | Django name | Purpose |
|---|---|---|
| `/` | `core:dashboard` | New SME main/home page |
| `/academy/` | `academy:index` | Academy shell and hash-routed Academy pages |
| `/academy/#tools` | client-side Academy route | Business Tools launcher |
| `/knowledge-hub/` | `knowledge_hub:index` | Knowledge Hub shell |
| `/inventory/` | `inventory:inventory` | Inventory tool; later receives preserved prototype presentation |
| `/tasks/` | `tasks:board` | Tasks tool; later receives preserved prototype presentation |
| `/accounts/profile/` | `accounts:profile` | Canonical profile route |

All pages require Django authentication. Login redirects to `core:dashboard`, and logout remains POST-only with CSRF protection.

### 5.2 Business Tools mapping

Replace hardcoded relative links in the Academy Tools view with URLs generated by Django and exposed through template data or a safe JSON route map.

| Tool card | Existing destination |
|---|---|
| CRM & Customers | `clients:list` |
| Invoicing | `billing:invoices` |
| Inventory | `inventory:inventory` |
| Projects & Tasks | `tasks:board` |
| Products & Services | `products:catalogue` |
| Purchasing | `purchasing:orders` |
| Sales Orders | `sales:orders` |
| Accounting | `accounting:ledger` |
| Payroll | `payroll:payroll`, permission-gated |
| Reports | `analytics:reports` |
| Documents | `documents:library` |
| Knowledge Hub | `knowledge_hub:index` |
| Marketing | prototype or “coming later” state until the final phase |

The tool registry should live in Python, not in several templates or JavaScript files. It must support permission filtering and a disabled/coming-later state.

## 6. Page-by-page integration method

Every page follows the same gated workflow:

1. Inventory visible fields, actions, filters, calculated values, and current sample state.
2. Map each item to an existing model/field/API action.
3. Classify unmatched items as a nullable addition, a new related model, static content, or out of scope.
4. Write failing model/API tests.
5. Add the smallest safe migration and service/API change.
6. Add `api.js` and replace durable local mutations with API calls.
7. Preserve CSS classes and markup wherever possible.
8. Verify permissions, validation, empty/loading/error states, and refresh persistence.
9. Run targeted tests and the full regression suite.
10. Complete an authenticated browser journey before declaring that page finished.

Do not migrate a whole module merely because one screen needs persistence. Each page should become independently usable before the next page starts.

## 7. Profile integration — first vertical slice

### 7.1 Field mapping

| Academy field | Current source | Decision |
|---|---|---|
| `name` | `User.first_name` + `User.last_name` | Reuse; render as full name and edit as two fields or parse explicitly |
| `email` | `User.email` | Reuse |
| `phone` | `User.phone` | Reuse and expose in the SME profile |
| avatar | `User.avatar` | Reuse |
| job title | `User.job_title` | Reuse |
| business name | Missing | Add to new one-to-one `SMEProfile` |
| location | Missing | Add to `SMEProfile` |
| industry | Missing | Add to `SMEProfile` |
| business stage | Missing | Add controlled choice to `SMEProfile` |
| reminder preference | Missing | Add to `SMEProfile` or dedicated preferences model |
| community digest | Missing | Add to `SMEProfile` or dedicated preferences model |
| compact cards | Browser presentation setting | Keep client-side unless cross-device persistence is approved |

### 7.2 New model

`apps.academy.models.SMEProfile`:

- `user`: one-to-one, cascade with the user;
- `business_name`: string, initially blank to support existing users;
- `location`: string, blank;
- `industry`: string or controlled vocabulary, blank initially;
- `business_stage`: choices `foundations`, `validate`, `build`, `grow`, `scale`, `investment_ready`;
- `learning_reminders`: boolean;
- `community_digest`: boolean;
- timestamps.

Create profiles lazily or with a data migration for existing users. Do not require a business name during the migration itself; require it only in the relevant form/API validation once users edit the SME profile.

### 7.3 Profile API

Provide an authenticated singleton endpoint such as `/api/v1/me/profile/` with `GET` and `PATCH`. It returns the User fields and nested SME profile fields needed by the page. Users may update only their own record. Role, department, staff status, and permissions remain read-only.

Both the existing Django profile form and the Academy profile page must update the same records. Add tests proving changes made through either surface are visible through the other.

## 8. Academy integration

### 8.1 Static-first catalogue

The 8 learning paths, 72 sample course records, module labels, resource descriptions, diagnostic questions, and educational copy may remain version-controlled during the first release. Before production content management, give every item a stable slug and validate references at startup or in tests.

### 8.2 Durable Academy records

Add only records representing user activity:

- `CourseEnrollment` — user, course slug, started/completed timestamps;
- `ModuleProgress` — enrollment, module index, status, completed timestamp;
- `PracticalOutput` — enrollment/module, response and timestamps;
- `QuizAttempt` — enrollment/module, answer, correctness, attempt timestamp;
- `DiagnosticAttempt` — user, version, answers JSON, computed result and timestamp;
- `MentorBooking` — user, mentor slug, requested date/time/topic and status;
- `EventRegistration` — user, event slug and status;
- `Certificate` — user, course slug, issued timestamp and immutable identifier;
- `AcademyActivity` — safe user-facing learning event summary.

Community posts and replies should be a separate task and may remain disabled until moderation, reporting, and permission rules are approved.

### 8.3 Academy APIs

Provide authenticated endpoints for current-user Academy summary, course progress, module completion, quiz attempts, practical outputs/reflections, diagnostics, bookings/registrations, certificates, and activity.

Completion operations must be idempotent. The backend, not JavaScript, enforces quiz and practical-output prerequisites.

## 9. Knowledge Hub integration

Keep articles, guides, courses, videos, templates, glossary terms, and official source links as curated catalogue content initially. Persist only user-specific activity:

- bookmarks;
- guide completion;
- course/lesson progress;
- quiz attempts and scores;
- video-preview completion;
- readiness checklist state;
- certificates where applicable.

Where Academy and Knowledge Hub share the same learning concept, use shared Academy progress services instead of duplicate tables. Use a content-source/type discriminator so progress can refer to an Academy course or a Knowledge Hub item without copying content into user-state rows.

Official compliance and funding links must remain clearly educational, open safely in a new tab, and be reviewed for currency before production releases.

## 10. Inventory integration

### 10.1 Reuse

Use the existing authorities:

- `products.Product` for SKU, name, type, description, sales price, cost price, tax rate, and active state;
- `inventory.StockLocation` for storage locations;
- `inventory.StockMovement` for receipts, issues, and adjustments;
- `inventory.ReorderRule` for minimum and reorder quantities;
- `purchasing.Supplier` for suppliers.

### 10.2 Expected schema gaps

Validate page fields before migration. Likely additions are product category, unit of measure, preferred supplier, barcode/image, movement reason/notes, supplier contact fields, and business-level inventory display settings.

Add fields as nullable/blank first. Preserve existing APIs for current screens while extending serializers for the SME inventory adapter.

### 10.3 Behavioural rules

- Product quantity is derived from stock movements, never directly edited.
- Archived products retain their movement history and SKU uniqueness.
- Stock writes go through domain services and database transactions.
- The API must enforce the agreed negative-stock policy.
- Reports use server-authoritative values.
- Remove the localStorage database only after API parity tests pass.

## 11. Tasks integration

### 11.1 Reuse

Use the existing `Board`, `BoardColumn`, `Task`, `TaskComment`, `TaskActivity`, `Project`, and `ProjectNotification` models and their `/api/v1/` endpoints.

### 11.2 Expected schema/API gaps

The prototype additionally expects project start date, owner, status, team display, and full editing. Validate and add only what remains necessary:

- `Project.start_date`, nullable;
- `Project.status`, controlled choices with a safe default;
- explicit owner if `created_by` is not sufficient;
- optional task-to-project relationship if the current project-card/subtask design cannot represent prototype tasks cleanly;
- API update support because the current `ProjectViewSet` allows only GET and POST;
- filters for personal, today, week, overdue, project, and calendar views.

Preserve server-authoritative board permissions. Drag/drop and status changes must use existing services so activity remains auditable.

## 12. Existing CRM tools

The initial integration changes navigation, not presentation, for Billing, Clients, Products, Purchasing, Sales, Accounting, Payroll, Documents, Analytics, Alerts, and other existing modules.

Each existing tool must receive:

- a working link from the SME Tools registry;
- a consistent route back to the SME home or Academy Tools page;
- existing authentication and permission enforcement;
- route and smoke tests;
- no CSS rewrite unless a broken layout prevents use.

A later visual-unification plan can migrate those templates to the SME design system after functional integration is complete.

## 13. Marketing — final phase

Do not implement Marketing while the preceding modules are incomplete. Preserve the prototype source and expose it as disabled, preview-only, or feature-flagged according to the product owner's choice.

Marketing ultimately needs models and APIs for brand profiles, campaigns/channels, adverts, content/assets, email drafts/templates, calendar activities, marketing leads and CRM conversion, performance snapshots, and consent/suppression/opt-out audit records.

Before implementation, decide whether marketing leads extend `clients.Client`, use a separate `Lead`, or use staged conversion. POPIA consent and suppression handling are release blockers for real message sending. Actual sending and social publishing remain separate integration projects.

## 14. API conventions

All new SME calls use `/api/v1/` and the shared client. The client must send same-origin cookies, attach CSRF to unsafe requests, support JSON/file uploads and DRF pagination, normalise errors, avoid unsafe automatic retries, and preserve `next` on authentication redirects.

New endpoints follow DRF serializers, viewsets/actions, and existing permission patterns. Business rules stay in `functionalities/<domain>/`, not templates or JavaScript.

## 15. Migration rules

1. Add nullable fields and new tables first.
2. Separate material data backfills from schema changes.
3. Backfill existing records deterministically.
4. Deploy tolerant readers before enforcing required values.
5. Add constraints only after data validation.
6. Never edit applied migration files.
7. Keep route/API compatibility during transition.
8. Back up production data and document rollback.
9. Test migrations against representative data, not only an empty SQLite database.

## 16. Security and permissions

- Require authentication on every SME page and user-state endpoint.
- Keep role and department read-only to ordinary users.
- Filter user-specific records by `request.user` server-side.
- Reuse existing object permissions for CRM tools.
- Validate files and ownership server-side.
- Escape user content rendered by JavaScript templates.
- Keep CSRF enabled.
- Retain educational disclaimers for learning, compliance, and funding content.
- Add moderation before public community posting.
- Never expose prototype sample people or analytics as real records.

## 17. Test strategy

Each vertical slice requires model/constraint tests, migration tests where existing data changes, service/idempotency tests, serializer/API validation tests, authentication/permission tests, route tests, focused JavaScript tests, an authenticated browser journey, and a full Django regression run.

Critical acceptance journeys:

1. Login lands on the SME home page.
2. Home opens Academy, Knowledge Hub, and available tools without broken relative links.
3. An Academy profile update appears in the current Django profile and survives refresh/login.
4. Course progress survives refresh and cannot bypass prerequisites.
5. Knowledge Hub bookmarks and progress survive refresh.
6. Inventory uses canonical product/stock/supplier records and preserves history.
7. Tasks uses canonical task APIs and stays visible on the current task screen.
8. Every Tools card resolves to an authorised route or clear unavailable state.
9. Marketing remains unavailable or preview-only until final-phase acceptance.

## 18. Delivery phases

### Phase 0 — Baseline and contract

Capture tests/migrations/routes/APIs, establish folders and asset conventions, define the Tools registry/flags, and protect reused routes with regression tests.

**Exit:** Existing behaviour is protected and integration contracts are testable.

### Phase 1 — SME main page and shell

Convert the SME main experience into the root Django page, move shared assets without changing appearance, add authenticated navigation/logout, implement the Tools registry, and add a return path from CRM pages.

**Exit:** Users land in the SME shell and can open every available tool.

### Phase 2 — Profile vertical slice

Add `apps.academy`, `SMEProfile`, safe migrations, `/api/v1/me/profile/`, the Academy Profile adapter, and bidirectional consistency with the existing Django form.

**Exit:** One canonical profile works through both interfaces.

### Phase 3 — Academy

Convert Academy to Django, separate catalogue data from user state, then add progress, outputs, quizzes, diagnostics, bookings, registrations, activity, and certificates incrementally. Leave community posting disabled until separately approved.

**Exit:** Core Academy learning journeys are durable and API-driven.

### Phase 4 — Knowledge Hub

Convert the page, reuse learning-state foundations, persist bookmarks/completion/quiz/readiness state, and validate curated links/disclaimers.

**Exit:** Personalised Knowledge Hub state is durable without duplicating Academy concepts.

### Phase 5 — Inventory

Map prototype fields, add approved nullable gaps, replace localStorage with adapters, and preserve stock history/current CRM behaviour.

**Exit:** The preserved Inventory frontend uses canonical CRM inventory data.

### Phase 6 — Tasks and projects

Map prototype screens, add approved project fields and API filters/update support, replace in-memory mutations, and verify assignments/moves/completion/activity/calendar.

**Exit:** The preserved Tasks frontend uses canonical CRM task data.

### Phase 7 — Existing-tool hardening

Verify all tool links and permissions, fix integration defects without broad restyling, run complete regression/browser suites, and document later visual work separately.

**Exit:** The SME shell and existing tools form one reliable authenticated application.

### Phase 8 — Marketing, last

Finalise lead/client and consent architecture, add models/services/APIs, convert the preserved page to API adapters, and keep external sending/publishing disabled pending integrations.

**Exit:** Marketing is database-backed, auditable, CRM-connected, and feature-flagged.

## 19. Definition of done

A page is complete only when Django serves it through an authenticated named route; its approved CSS remains intact; durable actions use `/api/v1/`; existing models are reused; migrations are additive/tested; backend permissions and validation are enforced; loading/empty/error states work; data survives refresh/login; targeted/full tests and the main browser journey pass; demo-only behaviour is documented; and unrelated CRM styling remains unchanged.

## 20. Immediate implementation order

1. Record the baseline: tests, migrations, URL names, APIs, and prototype assets.
2. Add the shared SME template/static folder structure.
3. Make the SME home page the authenticated root route.
4. Add the Python-owned Tools registry and CRM destinations.
5. Add shared navigation, logout, and return-to-SME behaviour.
6. Add `apps.academy`, `SMEProfile`, and profile API tests.
7. Connect the Academy Profile page end to end.
8. Convert the rest of Academy one vertical slice at a time.
9. Convert Knowledge Hub using shared learning-state services.
10. Convert Inventory to existing operational APIs.
11. Convert Tasks to existing task/project APIs.
12. Harden all existing-tool links and regression journeys.
13. Plan and implement Marketing only after steps 1–12 are accepted.

Do not begin with Marketing, do not restyle existing CRM tools during these phases, and do not remove the imported prototype until every converted page has passed its persistence and browser acceptance journey.
