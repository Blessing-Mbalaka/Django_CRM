# Phase 2 Operations and Accounting API

Phase 2 introduces the shared catalogue, authoritative stock ledger, purchasing, sales orders, and double-entry accounting foundations. New clients should use `/api/v1/`; `/api/` remains a compatibility alias.

## Accounting

| Endpoint | Purpose |
|---|---|
| `/api/v1/accounts/` | Chart of accounts |
| `/api/v1/accounting-periods/` | Open and closed posting periods |
| `/api/v1/journals/` | Create and inspect immutable journal entries |
| `/api/v1/journals/{id}/post/` | Validate and post a balanced draft journal |

Journal creation accepts nested lines:

```json
{
  "date": "2026-08-26",
  "reference": "DEP-001",
  "description": "Customer receipt",
  "lines": [
    {"account": 1, "debit": "115.00", "credit": "0.00"},
    {"account": 4, "debit": "0.00", "credit": "115.00"}
  ]
}
```

Rules:

- Each line contains a debit or credit, never both or neither.
- An entry requires at least two lines.
- Posting requires equal, non-zero debit and credit totals.
- Closed accounting periods reject posting.
- Journal entries cannot be edited or deleted through the API. Corrections will use reversal entries in the next accounting increment.

## Products and inventory

| Endpoint | Purpose |
|---|---|
| `/api/v1/products/` | Shared stock item and service catalogue |
| `/api/v1/stock-locations/` | Warehouses and stock locations |
| `/api/v1/stock-movements/` | Append-only receipts, issues, and adjustments |
| `/api/v1/reorder-rules/` | Minimum and suggested reorder quantities |

Stock is calculated from movements rather than a separately editable balance. Issues and negative adjustments are rejected when they would make stock negative. Service products cannot receive stock movements.

Filters: `/stock-movements/?product={id}&location={id}` and `/products/?type=stock|service`.

## Purchasing

| Endpoint | Purpose |
|---|---|
| `/api/v1/suppliers/` | Supplier register |
| `/api/v1/purchase-orders/` | Purchase order headers and totals |
| `/api/v1/purchase-order-lines/` | Draft purchase order lines |
| `/api/v1/purchase-orders/{id}/approve/` | Validate and number a purchase order |
| `/api/v1/purchase-orders/{id}/receive/` | Create a goods receipt and stock movements |
| `/api/v1/goods-receipts/` | Read-only receipt history |

Purchase order lifecycle:

```text
Draft → Approved (PO number allocated) → Received (stock receipt posted)
```

Only draft orders and lines can be edited or deleted. A purchase order can be received once; the transaction rolls back if any stock movement fails.

## Sales orders

| Endpoint | Purpose |
|---|---|
| `/api/v1/sales-orders/` | Customer sales orders and totals |
| `/api/v1/sales-order-lines/` | Draft sales order lines |
| `/api/v1/sales-orders/{id}/confirm/` | Validate and allocate a sales-order number |
| `/api/v1/sales-orders/{id}/invoice/` | Generate and issue a linked customer invoice |
| `/api/v1/sales-orders/{id}/fulfil/` | Create fulfilment and stock issues |
| `/api/v1/fulfilments/` | Read-only fulfilment history |

Sales lifecycle:

```text
Draft → Confirmed → Invoice and/or Fulfilment
```

Stock items require a location. Fulfilment is transactional and fails without sufficient stock. Service lines are invoiced but do not affect inventory. A sales order can generate only one invoice.

## Permissions and current boundary

- Authenticated users can read Phase 2 resources.
- Dean, Director, and Administrator roles can create or change operational and financial resources.
- Stock movements, goods receipts, fulfilments, issued invoices, and posted journals are protected from ordinary destructive edits.
- Organisation tenancy, purchase supplier bills, partial receipts/fulfilments, returns, accounting reversals, automatic sub-ledger posting, bank reconciliation, and the Phase 2 HTML/JavaScript screens remain subsequent increments.
