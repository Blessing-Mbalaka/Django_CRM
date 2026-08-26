# Phase 2 Operations and Accounting API

Phase 2 introduces the shared catalogue, authoritative stock ledger, purchasing, sales orders, and double-entry accounting foundations. New clients should use `/api/v1/`; `/api/` remains a compatibility alias.

## Accounting

| Endpoint | Purpose |
|---|---|
| `/api/v1/accounts/` | Chart of accounts |
| `/api/v1/accounting-periods/` | Open and closed posting periods |
| `/api/v1/journals/` | Create and inspect immutable journal entries |
| `/api/v1/journals/{id}/post/` | Validate and post a balanced draft journal |
| `/api/v1/journals/{id}/reverse/` | Post a dated reversing journal entry |

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
- Journal entries cannot be edited or deleted through the API. A posted entry can be reversed once; the original is retained and marked `reversed`.
- Chart-of-account system roles identify the bank, receivables, payables, revenue, VAT, expense and inventory control accounts.
- Issued invoices, customer payments, approved expenses and posted supplier bills create balanced journals automatically when their required system roles are configured. With no roles configured, legacy workflows continue without posting; incomplete configurations are rejected.

### Financial statements

| Endpoint | Parameters |
|---|---|
| `/api/v1/accounting/reports/trial-balance/` | `as_of=YYYY-MM-DD` |
| `/api/v1/accounting/reports/income-statement/` | `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` |
| `/api/v1/accounting/reports/balance-sheet/` | `as_of=YYYY-MM-DD` |

Reports are calculated directly from posted and reversed ledger entries. A reversed entry and its equal-and-opposite reversal are both retained in the reporting population, preserving the audit trail while netting to zero. The balance sheet includes cumulative current retained earnings and both the trial balance and balance sheet return an `is_balanced` control flag.

### Bank reconciliation

| Endpoint | Purpose |
|---|---|
| `/api/v1/bank-statements/` | Import and inspect statements with nested transactions |
| `/api/v1/bank-statement-lines/{id}/candidates/` | Find unused, exact-amount ledger candidates in the statement period |
| `/api/v1/bank-statement-lines/{id}/reconcile/` | Match a statement line to a posted bank-account journal line |
| `/api/v1/bank-statement-lines/{id}/unreconcile/` | Remove a match and reopen the statement |

Statement amounts are signed from the bank account perspective: deposits are positive and payments are negative. Imports require `opening_balance + sum(lines) = closing_balance`, all transaction dates must fall in the statement period, and only an account assigned the Bank / Cash system role can be used. A statement becomes reconciled when every line is matched.

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
| `/api/v1/purchase-orders/{id}/create-bill/` | Create a draft supplier bill after full receipt |
| `/api/v1/goods-receipts/` | Read-only receipt history |
| `/api/v1/supplier-bills/` | Inspect supplier bills |
| `/api/v1/supplier-bills/{id}/post/` | Post a supplier bill and payable journal |

Purchase order lifecycle:

```text
Draft → Approved (PO number allocated) → Received (stock receipt posted)
```

Only draft orders and lines can be edited or deleted. Receiving accepts an optional `lines` array of `{ "line": id, "quantity": amount }`; omitting it receives every outstanding quantity. Each receipt is retained separately and the transaction rolls back if any stock movement fails. A supplier bill can be created once the order is fully received.

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

Stock items require a location. Fulfilment accepts the same optional line/quantity shape as receiving, is transactional, and fails without sufficient stock. Service lines are invoiced but do not affect inventory. Each fulfilment is retained separately and a sales order can generate only one invoice.

## Permissions and current boundary

- Authenticated users can read Phase 2 resources.
- Dean, Director, and Administrator roles can create or change operational and financial resources.
- Stock movements, goods receipts, fulfilments, issued invoices, and posted journals are protected from ordinary destructive edits.
- Organisation tenancy, returns, statement-file parsers and bank-feed adapters, report exports, and authoritative `FinancialRecord` reconciliation remain subsequent increments.

## Phase 2 application screens

| Module | Route | JavaScript module |
|---|---|---|
| Products & Services | `/products/` | `modules/products/catalogue.js` |
| Inventory | `/inventory/` | `modules/inventory/inventory.js` |
| Purchasing | `/purchasing/` | `modules/purchasing/orders.js` |
| Sales Orders | `/sales/` | `modules/sales/orders.js` |
| Accounting | `/accounting/` | `modules/accounting/ledger.js`, `reports.js`, `reconciliation.js` |

These pages use the shared API transport, UJ SME component stylesheet, authenticated Django shell, and app-specific frontend modules. Operational validation and state transitions remain server-side.
