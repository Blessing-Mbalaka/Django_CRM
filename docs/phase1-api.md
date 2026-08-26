# Phase 1 SME API Contract

This document describes the backend-first contract for the first SME modules. All endpoints require Django session or DRF token authentication. New clients should use `/api/v1/`; the existing `/api/` prefix remains as a compatibility alias.

## Documents

| Endpoint | Methods | Purpose |
|---|---|---|
| `/api/document-libraries/` | GET, POST | Personal document libraries |
| `/api/document-folders/` | GET, POST, PATCH, DELETE | Folder hierarchy |
| `/api/documents/` | GET, POST, PATCH, DELETE | Document metadata; DELETE moves to Trash |
| `/api/documents/?trash=true` | GET | Trashed documents |
| `/api/documents/{id}/restore/` | POST | Restore a soft-deleted document |
| `/api/document-versions/` | GET, POST multipart | Immutable file-version upload and history |

Uploads accept `document` and `file` as multipart fields. The backend records original filename, MIME type, byte size, version number and SHA-256 checksum. The current development limit is 25 MB.

## Tasks and Kanban

| Endpoint | Methods | Purpose |
|---|---|---|
| `/api/task-boards/` | GET, POST, PATCH, DELETE | Boards; creation adds five default columns |
| `/api/task-columns/` | GET, POST, PATCH, DELETE | Configurable board columns |
| `/api/tasks/` | GET, POST, PATCH, DELETE | Persistent task cards |
| `/api/tasks/{id}/move/` | POST | Transactional column/order move |
| `/api/task-comments/` | GET, POST, PATCH, DELETE | Task discussion |
| `/api/task-activity/` | GET | Append-only task movement history |

Move payload:

```json
{
  "column": 4,
  "position": 0
}
```

Task list filters: `?board={id}` and `?assignee={user_id}`.

## Invoicing and payments

| Endpoint | Methods | Purpose |
|---|---|---|
| `/api/invoices/` | GET, POST, PATCH, DELETE | Invoice headers and computed totals |
| `/api/invoice-lines/` | GET, POST, PATCH, DELETE | Draft invoice lines |
| `/api/invoices/{id}/issue/` | POST | Validate and allocate the next invoice number |
| `/api/payments/` | GET, POST | Record a payment and update invoice status |

Invoice writes require Dean, Director or Administrator access. Issued invoice lines cannot be edited or deleted. Payments cannot be recorded on draft/void invoices or exceed the outstanding balance.

## Expenses

| Endpoint | Methods | Purpose |
|---|---|---|
| `/api/expense-categories/` | GET; management writes | Expense categories |
| `/api/expenses/` | GET, POST, PATCH, DELETE | Expense capture and filtering |
| `/api/expenses/{id}/submit/` | POST | Submit a draft/rejected expense |
| `/api/expenses/{id}/approve/` | POST | Management approval |
| `/api/expenses/{id}/reject/` | POST | Management rejection with optional comment |

Expense list filter: `?status=draft|submitted|approved|rejected|paid`. Ordinary staff see their own expenses; management roles can review all expenses.

## Frontend module layout

The frontend implements transport logic independently from page behaviour:

```text
static/js/
  api/
    client.js             # CSRF/token headers, JSON parsing, common errors
    documents-api.js
    tasks-api.js
    billing-api.js
    expenses-api.js
  modules/
    documents/library.js  # Folder/list/grid/details interactions
    tasks/kanban.js        # Drag/drop and accessible move controls
    billing/invoices.js
    expenses/expenses.js
```

Rules for JavaScript modules:

- A module imports its domain API wrapper; it does not call `fetch` directly.
- `client.js` is the only place that handles CSRF, authentication failures and common response parsing.
- API wrappers return data or throw a normalised error; they do not manipulate the DOM.
- UI modules own DOM events and rendering, but never reproduce state-transition or financial rules.
- Use progressive enhancement so standard forms and keyboard-accessible controls remain available where possible.

Authenticated application pages:

| Page | Route | Frontend module |
|---|---|---|
| Document library | `/documents/` | `modules/documents/library.js` |
| Tasks and Kanban | `/tasks/` | `modules/tasks/kanban.js` |
| Invoicing and billing | `/billing/` | `modules/billing/invoices.js` |
| Expense tracking | `/expenses/` | `modules/expenses/expenses.js` |

All four pages inherit the existing Django base shell and UJ theme. Shared SME components are defined in `static/css/sme_suite.css`.

## Current boundary

This phase establishes API, persistence, and the initial API-driven application screens. Private object storage, malware scanning, organisation tenancy, shared document permissions, double-entry posting, and PDF generation remain subsequent delivery gates from the master plan.
