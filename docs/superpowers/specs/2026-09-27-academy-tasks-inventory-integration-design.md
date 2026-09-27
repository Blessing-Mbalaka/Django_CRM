# Academy Landing, Tasks, and Inventory Integration Design

**Date:** 27 September 2026  
**Status:** Approved for implementation planning  
**Application:** JBS SME Ecosystem

## 1. Purpose

Make the Django SME Academy the canonical authenticated landing experience and replace the current Tasks and Inventory mini-app screens with complete, database-backed workspaces matching the supplied SME prototypes.

The delivery must preserve the reference layouts, responsive sidebars, navigation icons, conditional page actions, hash-based subpages, and interaction patterns while replacing prototype-only in-memory or browser-storage data with authenticated Django ORM and DRF workflows.

## 2. Canonical application entry point

- `/academy/` is the sole canonical authenticated landing page.
- Authenticated requests to `/` redirect to `/academy/`.
- `LOGIN_REDIRECT_URL` remains `/academy/`.
- The Academy opens at `#dashboard` when no hash is present.
- Academy Business Tools links use the canonical `/tasks/` and `/inventory/` routes.
- Tasks and Inventory return links point to `/academy/#tools`.
- The old root CRM dashboard is no longer rendered at `/`; its tool catalogue remains available through the Academy Business Tools section.

## 3. Shared interface architecture

Tasks and Inventory each use one Django-rendered application shell with client-side hash routing. The shell receives authenticated user metadata, permission flags, and named API endpoint URLs through safely serialized Django configuration. JavaScript must not hardcode a host, port, user identifier, or CSRF token.

The live implementations use maintained templates and assets under `templates/` and `static/`. Files under `SMEs (3)/SMEs/` remain visual and behavioral references and are not loaded as live application code.

Each workspace must:

- match the corresponding prototype's desktop and mobile layout;
- preserve its unique sidebar icons and active states;
- preserve browser back/forward navigation across hash routes;
- expose page-specific primary actions only when relevant and permitted;
- use native dialogs and locally maintained styling rather than requiring Bootstrap modal behavior;
- provide accessible loading, empty, success, validation, and failure states;
- retain entered form values after recoverable API failures;
- use the authenticated Django/DRF boundary for all persisted data.

Invalid or incomplete hash routes return safely to the workspace dashboard. Nested identifiers that do not exist or are not accessible show a not-found state without leaking inaccessible record details.

## 4. Tasks and project management workspace

### 4.1 Routes and screens

`/tasks/` supports these hash routes:

- `#dashboard`
- `#projects`
- `#project/<id>`
- `#tasks`
- `#my`
- `#calendar`
- `#team`

The sidebar also includes a return to `/academy/#tools` and authenticated sign-out.

The page-level primary action is conditional:

- Projects displays `New Project`.
- Dashboard, Project Details, Tasks, My Tasks, and Calendar display `New Task` where the user has permission to create one in the selected context.
- Team does not display an unrelated creation action.

### 4.2 Canonical three-state workflow

Every task board uses exactly:

1. `To Do`
2. `In Progress`
3. `Completed`

A data migration converts existing default columns without losing tasks or activity history:

- `Backlog` and `To Do` become `To Do`.
- `In Progress` and `Blocked` become `In Progress`.
- `Done` becomes `Completed`.

Tasks retain stable identifiers, assignments, due dates, parent relationships, project relationships, and activity records. Positions are rewritten contiguously inside each destination column. Newly created boards receive only the three canonical columns.

Moving a task into `Completed` sets `completed_at` when it is empty. Moving it out clears `completed_at`. Overdue remains a calculated display condition for unfinished tasks whose due date is before the local current date; it is not a fourth column.

### 4.3 Projects

The existing `Project` model remains canonical and gains:

- a start date;
- a persisted status with `Planning`, `Active`, `On Hold`, and `Completed` choices.

`created_by` is the project owner. `assignees` are the project team. Existing project Kanban cards, subtasks, and notifications remain supported.

Project progress is calculated from its project card's subtasks when present. If a project has no subtasks, progress is zero until its project card is completed, at which point it is 100 percent.

Project creation, update, and detail screens use database records. Due dates cannot precede start dates. Project status and task status are related for display but are not silently rewritten in both directions.

### 4.4 Task screens

- Dashboard calculates active projects, tasks due today, completed tasks, overdue tasks, project progress, and status distribution from accessible database records.
- Projects lists accessible projects and opens persisted project details.
- Tasks supports list and three-column board views, search, and All/To Do/In Progress/Completed/Overdue filters.
- My Tasks shows only the authenticated user's assignments with Today, This Week, Overdue, and Completed filters. Weeks run Monday through Sunday.
- Calendar renders a Monday-first six-week month grid. Previous, Today, and Next change the viewed month. Task and project due dates open their existing detail/edit flows.
- Team lists active users visible to the current workspace and calculates active, completed, and due-today counts from tasks the current user may access.

### 4.5 Genuine task attachments

Task attachments are real uploads, not filename placeholders. A dedicated attachment record stores:

- task;
- file;
- original filename;
- MIME type;
- size;
- SHA-256 checksum;
- uploader;
- creation timestamp.

Uploads reuse the current document rules: maximum 25 MB and the existing supported PDF, Word, Excel, JPEG, PNG, and plain-text MIME types. Files use Django's configured storage. Downloading an attachment goes through a protected Django endpoint that applies the same board/task access rule as the task; the UI does not expose a raw public media URL.

### 4.6 Task permissions

- Board owners can manage their boards, projects, columns, and tasks.
- Assigned users can see shared boards, projects, project cards, and tasks already made available by the existing access model.
- Assigned users can move and complete accessible assigned work.
- Creation, editing, deletion, upload, and download permissions are enforced by backend querysets and services, not only by hidden controls.
- Users receive no information about boards, projects, tasks, users, or attachments outside their accessible queryset.

## 5. Inventory workspace

### 5.1 Routes and screens

`/inventory/` supports these hash routes:

- `#dashboard`
- `#products`
- `#categories`
- `#in`
- `#out`
- `#suppliers`
- `#history`
- `#low`
- `#reports`
- `#settings`

The sidebar also includes a return to `/academy/#tools` and authenticated sign-out.

Actions are conditional by page and permission. Examples include Add Product on product-oriented pages, Add Category on Categories, Add Supplier on Suppliers, movement submission on Stock In/Out, export or print on Reports, and management-only backup/clear controls in Settings.

### 5.2 Shared records and inventory-specific metadata

`products.Product` remains the only canonical product record. `purchasing.Supplier` remains the only canonical supplier record. Inventory must not create parallel product or supplier tables.

Inventory adds:

- `InventoryCategory`: name, description, active state, and timestamps;
- `ProductInventoryProfile`: one-to-one product relationship, category, unit of measure, preferred supplier, and stock reference;
- `InventorySettings`: singleton configuration for business name, currency, default unit, default reorder level, and low-stock alerts.

The shared supplier gains optional contact-person, address, and notes fields required by the Inventory interface. Existing Purchasing relations remain valid.

Product SKU, name, description, cost price, selling price, type, and active state remain on `Product`. SKUs stay unique across active and archived records. Product removal from the Inventory interface sets `is_active=False`; it does not delete stock or purchasing history.

Existing products without an inventory profile remain readable and receive default display values. A profile is created when inventory-specific details are first saved.

### 5.3 Stock authority and arithmetic

`StockMovement` remains the sole source of quantity changes. Product quantity is never edited directly.

- Stock In creates a receipt or positive adjustment.
- Stock Out creates an issue or negative adjustment.
- Stock-out services lock the relevant movement scope within a transaction and reject a result below zero.
- History retains product and supplier context required to understand past movements.
- Current quantity is calculated per product and location and may be aggregated for product-level screens.
- Existing location-specific `ReorderRule` records remain authoritative.
- A product/location is low stock when on-hand quantity is greater than zero and less than or equal to its minimum rule.
- A product/location is out of stock when on-hand quantity is zero or below; negative persisted stock is prohibited.

When no explicit reorder rule exists, the Inventory Settings default reorder level is used for display and new-product setup. Unit totals that mix units are labelled as aggregate quantities rather than implied to be directly comparable.

### 5.4 Inventory behavior

- Dashboard shows active products, aggregate units, inventory value, low-stock counts, out-of-stock counts, status distribution, and recent movements from the database.
- Products supports search, category/status filters, sorting, create/edit/detail, and archive.
- Categories supports search and create/edit. A category assigned to a product cannot be deleted; it may be deactivated.
- Stock In and Stock Out validate product, location, quantity, date, reason/reference, supplier where applicable, and the resulting balance.
- Suppliers uses shared supplier data. Removal deactivates a supplier when history or purchasing records exist and never removes historical names or relations.
- Stock History supports product, movement type, date range, text, and reason/reference filters and CSV export.
- Low Stock lists low and out-of-stock product/location rows and links to replenishment actions.
- Reports supports Current Stock Summary, Inventory Value, Low Stock, Out of Stock, Stock Movement Summary, and Products by Category. Data and CSV exports are generated from current persisted records.
- Settings persists configuration, provides a JSON inventory backup, and provides a separately confirmed management-only clear-data operation.

Clear-data removes inventory movements, reorder rules, inventory profiles, and inventory categories in one transaction. It does not delete shared Products, Suppliers, Purchasing records, or Inventory Settings. Products created through Inventory are archived rather than deleted when their inventory profile is cleared. The operation returns an explicit summary of affected record counts.

### 5.5 Inventory permissions

Authenticated users may read the inventory pages and records available under the existing application boundary. Inventory writes use the existing CEO/Director/System Administrator policy. The UI hides unavailable mutation controls, while every API mutation independently enforces the policy.

Settings changes, backup access, and clear-data require the same management role. Destructive actions require an explicit confirmation that names the affected scope.

## 6. API and service boundaries

Existing `/api/v1/` routes remain canonical and are extended rather than duplicated.

Tasks adds or extends explicit endpoints for:

- task dashboard summaries;
- accessible team summaries;
- task attachment upload/list/download/delete;
- project update fields;
- calendar queries bounded by a requested date range.

Inventory adds or extends explicit endpoints for:

- categories;
- inventory product summaries and profiles;
- supplier fields required by Inventory;
- current stock summaries;
- low-stock summaries;
- report datasets and CSV responses;
- singleton settings;
- JSON backup;
- transactional clear-data.

Multi-record mutations and stock calculations live in focused functions under `functionalities/tasks/` and `functionalities/inventory/`. Views and serializers remain thin. Query parameters are validated and bounded; calendar and report endpoints do not return unbounded unrelated history.

## 7. Validation, feedback, and failure handling

- Serializer and service validation is authoritative.
- Field errors appear beside the related input; non-field errors appear at the top of the dialog or page.
- Submit buttons are disabled while a request is pending.
- Recoverable failures retain entered values and provide a retry path.
- Successful writes close the relevant dialog, announce an accessible toast/status message, and refresh only the affected data.
- Concurrent stock writes cannot create negative stock.
- Protected or referenced inventory records are deactivated/archived with a clear response rather than failing silently or cascading into history.
- Network, permission, and not-found responses have distinct user-facing messages without exposing server internals.

## 8. Testing strategy

### 8.1 Migration and model tests

- Root requests redirect to `/academy/` for authenticated users.
- The column migration produces exactly three ordered columns per board and preserves task IDs, assignments, positions, parents, projects, and activity records.
- Moving into and out of Completed updates `completed_at` correctly.
- Project date validation rejects due dates before start dates.
- Inventory profile defaults work for pre-existing products.
- Category assignment protection, supplier deactivation, SKU uniqueness, and settings singleton behavior are enforced.
- Concurrent or sequential stock-out attempts cannot produce negative stock.

### 8.2 API and permission tests

- Unauthenticated requests follow the configured authentication boundary.
- Users cannot enumerate inaccessible task/project/attachment records.
- Board owners and assignees receive only the approved task capabilities.
- Attachment MIME, size, checksum, upload, protected download, and deletion rules are tested using temporary media storage.
- Inventory readers and management writers receive the correct access.
- Every inventory CRUD/report/settings/backup/clear endpoint persists or returns real database state.
- Clear-data is atomic and leaves shared Product, Supplier, and Purchasing records intact.

### 8.3 Template and browser tests

Browser journeys cover desktop and mobile widths and assert no unhandled JavaScript errors or HTTP 500 responses.

Tasks journeys cover all seven hash routes, project detail, creation/editing, list/board filters, three-state moves, My Tasks periods, month navigation, team metrics, assignment visibility, completion, genuine attachment upload, and protected download.

Inventory journeys cover all ten hash routes, product/category/supplier workflows, stock in/out, insufficient-stock rejection, history filters, low-stock calculations, all reports, CSV export, settings persistence, backup, and role-restricted clear-data.

Academy journeys cover the canonical landing page, root redirect, Business Tools links, return links, and role-conditional controls. The full Django test suite and the existing Academy browser journeys must remain green.

## 9. Delivery boundaries

This delivery includes the canonical Academy redirect, complete Tasks and Inventory workspaces, additive and data migrations, protected uploads, API/service extensions, responsive SME styling, role-aware controls, automated Django tests, browser acceptance journeys, and updates to affected project documentation.

It does not introduce a new organisation/tenant model, replace Django's configured media storage, import prototype sample records, redesign unrelated CRM modules, or create duplicate Product, Supplier, User, or Staff records.

## 10. Acceptance criteria

The feature is accepted when:

- `/academy/` is the canonical authenticated landing page and `/` redirects to it;
- Tasks visually and behaviorally matches the supplied task prototype across every hash route;
- all boards use the exact three-state workflow without loss of existing task data;
- task attachments are genuine validated uploads with protected access;
- Inventory visually and behaviorally matches the supplied inventory prototype across every hash route;
- all screens read and write the existing Django database rather than prototype state;
- shared Products, Suppliers, Users, and stock history remain canonical and consistent across apps;
- conditional icons and page actions match each workspace and the authenticated user's permissions;
- desktop and mobile browser journeys pass without unhandled client or server errors;
- targeted tests and the complete Django suite pass.
