# Financial Master Plan

## Objective

The accounting ledger is the single source of truth for every completed financial event. Operational modules own their workflow data, but they never maintain a second copy of actual revenue, expense, cash, receivable, payable, inventory value, or profit.

`FinancialRecord` is retained only for pipeline forecasts. Actual reporting is calculated from posted journal entries and linked source documents.

## Canonical event flow

| Operational event | Debit | Credit | Recognition point |
|---|---|---|---|
| Customer invoice issued | Accounts receivable (gross) | Sales revenue (net), output VAT | Accrual revenue |
| Customer payment | Bank | Accounts receivable | Cash collection |
| Supplier bill posted, stock | Inventory, input VAT | Accounts payable | Inventory ownership |
| Supplier bill posted, service | General expense, input VAT | Accounts payable | Expense incurred |
| Supplier payment | Accounts payable | Bank | Cash payment |
| Staff expense approved | General expense, input VAT | Accounts payable | Expense accepted |
| Staff expense paid | Accounts payable | Bank | Cash reimbursement/payment |
| Stock fulfilled to customer | Cost of goods sold | Inventory | Stock leaves the business |
| Payroll approved | Payroll expense | Payroll payable and statutory liabilities | Payroll incurred |
| Payroll paid | Payroll payable | Bank | Employees paid |

VAT is never included in revenue or recoverable expense. Product purchases remain inventory until fulfilment. Payroll expense is gross pay plus employer UIF; net pay is a liability until paid.

## Ownership rules

- Products define whether an item is stock or service and provide default selling and reference cost data.
- Inventory movements are the quantity and inventory-cost audit trail. Fulfilment issues use the current weighted-average cost.
- Sales orders control quantities and prices; issued invoices recognize revenue.
- Purchase orders control ordered and received quantities; supplier bills recognize inventory, expense, VAT, and payables.
- Expenses control submission and approval; approval recognizes a payable and payment clears it.
- Payroll controls payslips; approval recognizes payroll cost and liabilities and payment clears employee net pay.
- Accounting owns balances, statements, reversals, and net profit.
- Finance owns pipeline forecasting and presents ledger-backed actuals.

## Integrity requirements

1. Every automatic journal is balanced and posted in an open period.
2. A source event can create at most one journal entry of each source type.
3. Workflow state and its journal entry commit in the same database transaction.
4. Missing or partially configured system accounts must produce a visible validation error once accounting is enabled.
5. Posted source documents are immutable; corrections use reversals and replacement documents.
6. Payments cannot exceed the remaining receivable or payable balance.
7. Inventory cannot become negative and an issue must carry a cost.
8. Reports use posted journals, never duplicated manually entered actuals.

## Reporting definitions

- Confirmed revenue: credits less debits in revenue accounts from posted entries.
- Expenses: debits less credits in expense accounts, including cost of goods sold and payroll.
- Net profit: confirmed revenue minus expenses.
- Cash received/paid: bank-account journal activity, reported separately from accrual revenue and expense.
- Unpaid invoices and bills: source-document balances, not a manually maintained flag.
- Pipeline: positive forecast records tied to engagements; it never enters the ledger.

## Migration and rollout

1. Configure all required system accounts (`python manage.py bootstrap_accounts` creates a safe default chart).
2. Deploy schema and posting services.
3. Reconcile existing invoices, payments, expenses, supplier bills, stock movements, and pay runs to journals.
4. Convert valid legacy `FinancialRecord` revenue/expense rows into reviewed opening or source-linked journals; archive duplicates.
5. Restrict new `FinancialRecord` writes to pipeline.
6. Compare trial balance, receivables, payables, inventory valuation, and bank reconciliation before cut-over.
7. Sign off the opening balances and then use ledger-backed dashboards exclusively.

## Acceptance tests

- Buy stock, receive it, post and pay the supplier bill: inventory and bank/payables agree.
- Sell and fulfil stock, issue and collect the invoice: revenue, VAT, receivables, COGS, inventory, and bank agree.
- Approve and pay a staff expense: expense/VAT, payable, and bank agree without double counting.
- Approve and pay payroll: payroll expense, employee/statutory liabilities, and bank agree.
- The Finance overview and accounting income statement return the same actual revenue, expenses, and net profit.
- Repeating an event does not create a duplicate journal.
