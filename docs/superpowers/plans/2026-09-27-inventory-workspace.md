# Inventory Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the movement-ledger-only inventory page with the complete prototype-matched, database-backed inventory workspace.

**Architecture:** Keep shared Product, Supplier, StockLocation, StockMovement, and ReorderRule records authoritative. Add inventory-specific category/profile/settings models, put stock arithmetic and reporting in focused services, expose explicit DRF resources/actions, and serve all ten reference screens through one hash-routed Django shell.

**Tech Stack:** Django 6.0, Django REST Framework 3.17, vanilla ES modules, native `<dialog>`, Django TestCase/APITestCase, Playwright

**Spec:** `docs/superpowers/specs/2026-09-27-academy-tasks-inventory-integration-design.md`

## Global Constraints

- Product and Supplier remain shared canonical records; no duplicate inventory product/supplier tables.
- Stock quantity changes only through StockMovement.
- Negative stock is prohibited under concurrent and sequential writes.
- Existing database records populate the UI; prototype sample records are not imported.
- SKUs stay unique across active and archived products.
- Referenced records are deactivated/archived rather than cascading into history.
- Inventory writes, settings, backup, and clear-data use the existing CEO/Director/System Administrator policy.

## Review Focus

- A pre-existing Product without an inventory profile must remain visible with deterministic defaults.
- Two stock-out requests against the same balance must not both succeed when their combined quantity exceeds stock.
- Mixed units must be labelled as aggregate quantities rather than presented as a comparable unit total.
- Clearing inventory data must preserve Product, Supplier, PurchaseOrder, and GoodsReceipt rows.
- CSV cells beginning with `=`, `+`, `-`, or `@` must be neutralized against spreadsheet formula injection.

---

### Task 1: Add inventory categories, profiles, settings, and supplier metadata

**Files:**
- Modify: `apps/inventory/models.py`
- Modify: `apps/purchasing/models.py`
- Create: `apps/inventory/migrations/0002_inventorycategory_inventorysettings_productprofile.py`
- Create: `apps/purchasing/migrations/0004_supplier_inventory_metadata.py`
- Modify: `apps/inventory/tests.py`
- Modify: `apps/purchasing/tests.py`

**Interfaces:**
- Produces: `InventoryCategory`, `ProductInventoryProfile`, `InventorySettings.load() -> InventorySettings`; supplier `contact_person`, `address`, and `notes`

- [ ] **Step 1: Write failing model/default tests**

Add separate tests for singleton settings creation, deterministic defaults, category case-insensitive uniqueness, profile defaults for an existing product, assigned-category deletion protection, and preservation of existing supplier relations after adding optional metadata.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryMetadataTests apps.purchasing.tests.SupplierInventoryMetadataTests -v 2`

Expected: FAIL because the models/fields are missing.

- [ ] **Step 3: Implement models and migrations**

Add category fields `name`, `description`, `is_active`, timestamps; profile fields `product` one-to-one, nullable category, `unit`, nullable preferred supplier, `stock_reference`; singleton settings fields from the spec with `load()` pinned to primary key 1. Add optional supplier fields without modifying existing values.

- [ ] **Step 4: Enforce category removal semantics**

Use `PROTECT` from profile to category and expose deactivation as the safe referenced-record path. Preserve `Product.is_active` as product archival.

- [ ] **Step 5: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryMetadataTests apps.purchasing.tests.SupplierInventoryMetadataTests -v 2`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/inventory apps/purchasing
git commit -m "feat: add inventory metadata models"
```

### Task 2: Harden stock arithmetic and build inventory queries

**Files:**
- Modify: `functionalities/inventory/services.py`
- Create: `functionalities/inventory/queries.py`
- Create: `functionalities/inventory/reports.py`
- Modify: `apps/inventory/tests.py`

**Interfaces:**
- Consumes: `record_movement(...)`, `stock_on_hand(*, product, location)`
- Produces: `product_stock_rows(queryset=None) -> list[dict]`, `low_stock_rows() -> list[dict]`, `inventory_summary() -> dict`, `movement_history(filters) -> QuerySet`, `report_dataset(name) -> {headers, rows, summary}`

- [ ] **Step 1: Write failing stock and query tests**

Add tests for sequential insufficient stock, locked stock-out service behavior, receipts/adjustments, existing product defaults, per-location rule thresholds, default minimum fallback, inactive-product exclusion, mixed-unit labelling, and deduplicated inventory value.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryServiceTests apps.inventory.tests.InventoryQueryTests -v 2`

Expected: FAIL on missing query interfaces and unlocked negative-stock edge cases.

- [ ] **Step 3: Implement transactional stock validation**

In `record_movement`, wrap writes in `transaction.atomic()`, lock the relevant product/location movement scope using a deterministic lock row (`ReorderRule` when present, otherwise `StockLocation`), recalculate on-hand inside the transaction, and reject outgoing quantities that exceed it.

- [ ] **Step 4: Implement summary/query functions**

Use ORM annotations and focused Python formatting to return product/location quantities, values, status, category, supplier, and unit. Apply `InventorySettings.default_reorder_level` only when no location rule exists.

- [ ] **Step 5: Implement report datasets and safe CSV cells**

Support exactly the six approved report names. Prefix dangerous spreadsheet-leading text with an apostrophe before CSV quoting. Keep archived products out of current reports while retaining their movements in history reports.

- [ ] **Step 6: Run focused tests**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryServiceTests apps.inventory.tests.InventoryQueryTests apps.inventory.tests.InventoryReportTests -v 2`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add functionalities/inventory apps/inventory/tests.py
git commit -m "feat: add inventory stock queries and reports"
```

### Task 3: Expose inventory metadata, summaries, reports, settings, and safe clearing

**Files:**
- Modify: `apps/inventory/serializers.py`
- Modify: `apps/inventory/api_views.py`
- Modify: `apps/purchasing/serializers.py`
- Modify: `apps/purchasing/api_views.py`
- Modify: `apps/api/urls.py`
- Create: `functionalities/inventory/maintenance.py`
- Modify: `apps/inventory/tests.py`

**Interfaces:**
- Produces: `InventoryCategoryViewSet`, `InventoryProductViewSet`, `InventorySettingsViewSet`
- Produces actions/routes for `summary`, `low-stock`, `reports`, `report.csv`, `backup`, and `clear-data`
- Produces: `clear_inventory_data(*, actor) -> dict[str, int]`

- [ ] **Step 1: Write failing API and permission tests**

Add individual tests for category/product-profile CRUD, product archive, supplier metadata update, reader GET access, denied reader mutations, manager mutations, filtered history, summary, low stock, every report, safe CSV output, singleton settings update, JSON backup structure, and clear-data permission.

- [ ] **Step 2: Write failing clear-data preservation test**

Create Products, Suppliers, PurchaseOrders, GoodsReceipts, profiles, categories, rules, and movements. Assert `clear_inventory_data` removes only inventory-owned operational rows/profiles/categories, archives affected products, preserves shared/purchasing rows, returns exact counts, and rolls back on an injected failure.

- [ ] **Step 3: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryWorkspaceApiTests apps.inventory.tests.InventoryClearDataTests -v 2`

Expected: FAIL because endpoints/services do not exist.

- [ ] **Step 4: Implement serializers and viewsets**

Expose explicit fields only. Use `IsAuthenticated` for reads and `IsCEODirectorOrAdmin` for mutations. Provide product summaries without permitting direct quantity writes. Extend the shared Supplier serializer with only the new metadata fields.

- [ ] **Step 5: Implement reports, backup, and transactional clear-data actions**

Return JSON datasets for UI reports and `text/csv` for export. Backup contains version, generated timestamp, settings, categories, product/profile data, suppliers, locations, reorder rules, and movements. Clear-data requires a confirmation token value `CLEAR INVENTORY DATA` and calls the atomic maintenance service.

- [ ] **Step 6: Run inventory and purchasing API tests**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests apps.purchasing.tests -v 2`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add apps/inventory apps/purchasing apps/api/urls.py functionalities/inventory
git commit -m "feat: expose complete inventory APIs"
```

### Task 4: Build the prototype-matched inventory shell and hash router

**Files:**
- Replace: `templates/inventory/inventory.html`
- Create: `static/sme/inventory/css/style.css`
- Create: `static/sme/inventory/js/api.js`
- Create: `static/sme/inventory/js/views.js`
- Create: `static/sme/inventory/js/reports.js`
- Create: `static/sme/inventory/js/app.js`
- Modify: `apps/inventory/views.py`
- Modify: `apps/inventory/tests.py`

**Interfaces:**
- Consumes: named endpoint configuration, authenticated user/permissions, and Inventory APIs from Task 3
- Produces hash routes `dashboard`, `products`, `categories`, `in`, `out`, `suppliers`, `history`, `low`, `reports`, and `settings`

- [ ] **Step 1: Write failing template/shell tests**

Assert `/inventory/` contains the inventory workspace shell, ten navigation routes with prototype labels/icons, business identity, `/academy/#tools`, sign-out form, native dialog, safely serialized configuration, management permission flag, and no generic topbar markers.

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests.InventoryWorkspaceTemplateTests -v 2`

Expected: FAIL against the current movement-ledger template.

- [ ] **Step 3: Build the Django shell and visual system**

Port the supplied inventory CSS into maintained static files, preserving sidebar widths, icons, cards, banner, tables, dialogs, responsive breakpoints, print rules, and accessible focus states. Use Django static URLs for assets.

- [ ] **Step 4: Implement the API adapter**

Provide explicit methods for products/profiles, categories, suppliers, locations, movements, reorder rules, summaries, reports/CSV, settings, backup, and clear-data through the shared CSRF-aware request behavior.

- [ ] **Step 5: Implement all ten renderers**

In `views.js`, render database-backed Dashboard, Products, Categories, Stock In/Out, Suppliers, History, Low Stock, and Settings. In `reports.js`, render the six server datasets and request CSV downloads. Escape all user-controlled strings.

- [ ] **Step 6: Implement routing and interactions**

In `app.js`, parse/normalize hashes, update active icons/titles/actions, manage filters/forms/dialogs, preserve failed form state, enforce permission-driven controls, preview stock movements, print reports, download backup, and require typed confirmation for clear-data.

- [ ] **Step 7: Run template and inventory tests**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests apps.purchasing.tests -v 2`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add templates/inventory static/sme/inventory apps/inventory/views.py apps/inventory/tests.py
git commit -m "feat: build complete inventory workspace"
```

### Task 5: Add inventory browser acceptance coverage

**Files:**
- Create: `tests/browser/test_inventory_workspace.py`
- Modify: `tests/browser/test_dummy_users.py`

**Interfaces:**
- Consumes: live Django server and demo users
- Produces: desktop/mobile inventory acceptance journey with uniquely prefixed fixtures

- [ ] **Step 1: Write the failing browser journey**

Cover login, ten hash routes, responsive sidebar, product/category/supplier workflows, stock receipt and issue, insufficient-stock feedback, history filtering, low-stock results, all six reports, CSV download, settings persistence, backup download, ordinary-user hidden mutations, and management-only typed clear confirmation. Capture page errors and HTTP 500 responses.

- [ ] **Step 2: Run against the development server and verify RED**

Run server: `.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`

Run: `.venv\Scripts\python.exe tests/browser/test_inventory_workspace.py`

Expected: FAIL at the first missing behavior before Task 4; afterward it should identify only integration defects.

- [ ] **Step 3: Fix browser-discovered integration defects through a failing automated assertion**

Keep fixes scoped to the failed behavior and rerun the focused Django or browser test before continuing.

- [ ] **Step 4: Run inventory and browser suites**

Run: `.venv\Scripts\python.exe manage.py test apps.inventory.tests apps.purchasing.tests -v 2`

Run: `.venv\Scripts\python.exe tests/browser/test_inventory_workspace.py`

Expected: PASS with no page errors or HTTP 500 responses.

- [ ] **Step 5: Commit**

```powershell
git add tests/browser/test_inventory_workspace.py tests/browser/test_dummy_users.py apps/inventory apps/purchasing functionalities/inventory templates/inventory static/sme/inventory
git commit -m "test: cover inventory workspace journeys"
```

### Task 6: Run whole-application regression and update documentation

**Files:**
- Modify: `Master Plan.md`
- Modify: `docs/release-checklist.md`
- Modify: `ReadME`

**Interfaces:**
- Consumes: completed Academy landing, Tasks, and Inventory plans
- Produces: verified release documentation and commands

- [ ] **Step 1: Update documentation**

Document `/academy/` as canonical landing, all Tasks/Inventory routes, three-state migration behavior, attachment rules, inventory permission boundary, backup/clear semantics, and browser-test commands.

- [ ] **Step 2: Run Django system checks and migration consistency**

Run: `.venv\Scripts\python.exe manage.py check`

Run: `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`

Expected: no issues and no model changes pending.

- [ ] **Step 3: Run the complete Django suite**

Run: `.venv\Scripts\python.exe manage.py test -v 2`

Expected: PASS. Report every pre-existing failure by exact test name if the baseline is not green.

- [ ] **Step 4: Run all browser journeys**

Run: `.venv\Scripts\python.exe tests/browser/test_dummy_users.py`

Run: `.venv\Scripts\python.exe tests/browser/test_academy_management.py`

Run: `.venv\Scripts\python.exe tests/browser/test_task_workspace.py`

Run: `.venv\Scripts\python.exe tests/browser/test_inventory_workspace.py`

Expected: PASS with no page errors or HTTP 500 responses.

- [ ] **Step 5: Commit**

```powershell
git add "Master Plan.md" docs/release-checklist.md ReadME
git commit -m "docs: document integrated SME workspaces"
```
