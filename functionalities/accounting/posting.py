from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.accounting.models import Account, JournalEntry
from .services import create_draft_entry, post_entry


def system_accounts(*roles):
    accounts = {account.system_role: account for account in Account.objects.filter(system_role__in=roles, is_active=True)}
    if not accounts:
        if Account.objects.filter(system_role__isnull=False).exists():
            raise ValidationError(f'Missing configured system accounts: {", ".join(roles)}.')
        return None
    missing = [role for role in roles if role not in accounts]
    if missing:
        raise ValidationError(f'Missing configured system accounts: {", ".join(missing)}.')
    return accounts


def post_source(*, source_type, source_id, date, reference, description, lines, user):
    existing = JournalEntry.objects.filter(source_type=source_type, source_id=source_id).first()
    if existing:
        return post_entry(entry=existing) if existing.status == JournalEntry.Status.DRAFT else existing
    entry = create_draft_entry(date=date, reference=reference, description=description, source_type=source_type, source_id=source_id, lines=lines, user=user)
    return post_entry(entry=entry)


def post_invoice(invoice):
    roles = [Account.SystemRole.ACCOUNTS_RECEIVABLE, Account.SystemRole.SALES_REVENUE]
    if invoice.tax_total:
        roles.append(Account.SystemRole.OUTPUT_VAT)
    accounts = system_accounts(*roles)
    if not accounts:
        return None
    lines = [
        {'account': accounts[Account.SystemRole.ACCOUNTS_RECEIVABLE], 'debit': invoice.total},
        {'account': accounts[Account.SystemRole.SALES_REVENUE], 'credit': invoice.subtotal},
    ]
    if invoice.tax_total:
        lines.append({'account': accounts[Account.SystemRole.OUTPUT_VAT], 'credit': invoice.tax_total})
    return post_source(source_type='invoice', source_id=invoice.id, date=invoice.issue_date, reference=invoice.number or '', description=f'Invoice issued to {invoice.client.name}', lines=lines, user=invoice.created_by)


def post_customer_payment(payment):
    accounts = system_accounts(Account.SystemRole.BANK, Account.SystemRole.ACCOUNTS_RECEIVABLE)
    if not accounts:
        return None
    return post_source(source_type='customer_payment', source_id=payment.id, date=payment.paid_on, reference=payment.reference, description=f'Payment for {payment.invoice.number}', lines=[{'account': accounts[Account.SystemRole.BANK], 'debit': payment.amount}, {'account': accounts[Account.SystemRole.ACCOUNTS_RECEIVABLE], 'credit': payment.amount}], user=payment.recorded_by)


def post_expense(expense, user):
    roles = [Account.SystemRole.ACCOUNTS_PAYABLE, Account.SystemRole.GENERAL_EXPENSE]
    if expense.vat_amount:
        roles.append(Account.SystemRole.INPUT_VAT)
    accounts = system_accounts(*roles)
    if not accounts:
        return None
    net = expense.amount - expense.vat_amount
    lines = [{'account': accounts[Account.SystemRole.GENERAL_EXPENSE], 'debit': net}, {'account': accounts[Account.SystemRole.ACCOUNTS_PAYABLE], 'credit': expense.amount}]
    if expense.vat_amount:
        lines.insert(1, {'account': accounts[Account.SystemRole.INPUT_VAT], 'debit': expense.vat_amount})
    return post_source(source_type='expense', source_id=expense.id, date=expense.incurred_on, reference=f'EXP-{expense.id}', description=expense.description, lines=lines, user=user)


def post_expense_payment(expense, user):
    accounts = system_accounts(Account.SystemRole.BANK, Account.SystemRole.ACCOUNTS_PAYABLE)
    if not accounts:
        return None
    return post_source(source_type='expense_payment', source_id=expense.id, date=expense.paid_on, reference=f'EXP-PAY-{expense.id}', description=f'Payment: {expense.description}', lines=[{'account': accounts[Account.SystemRole.ACCOUNTS_PAYABLE], 'debit': expense.amount}, {'account': accounts[Account.SystemRole.BANK], 'credit': expense.amount}], user=user)


def post_supplier_bill(supplier_bill):
    from apps.products.models import Product
    roles = [Account.SystemRole.ACCOUNTS_PAYABLE]
    if supplier_bill.tax_total:
        roles.append(Account.SystemRole.INPUT_VAT)
    order_lines = list(supplier_bill.purchase_order.lines.select_related('product'))
    if any(line.product.product_type == Product.Type.STOCK for line in order_lines):
        roles.append(Account.SystemRole.INVENTORY)
    if any(line.product.product_type == Product.Type.SERVICE for line in order_lines):
        roles.append(Account.SystemRole.GENERAL_EXPENSE)
    accounts = system_accounts(*roles)
    if not accounts:
        return None
    inventory_total = sum((line.line_total for line in order_lines if line.product.product_type == Product.Type.STOCK), Decimal('0.00'))
    expense_total = supplier_bill.subtotal - inventory_total
    lines = []
    if inventory_total:
        lines.append({'account': accounts[Account.SystemRole.INVENTORY], 'debit': inventory_total})
    if expense_total:
        lines.append({'account': accounts[Account.SystemRole.GENERAL_EXPENSE], 'debit': expense_total})
    if supplier_bill.tax_total:
        lines.append({'account': accounts[Account.SystemRole.INPUT_VAT], 'debit': supplier_bill.tax_total})
    lines.append({'account': accounts[Account.SystemRole.ACCOUNTS_PAYABLE], 'credit': supplier_bill.total})
    return post_source(source_type='supplier_bill', source_id=supplier_bill.id, date=supplier_bill.bill_date, reference=supplier_bill.supplier_invoice_number, description=f'Supplier bill from {supplier_bill.purchase_order.supplier.name}', lines=lines, user=supplier_bill.created_by)


def post_supplier_payment(payment):
    accounts = system_accounts(Account.SystemRole.BANK, Account.SystemRole.ACCOUNTS_PAYABLE)
    if not accounts:
        return None
    return post_source(source_type='supplier_payment', source_id=payment.id, date=payment.paid_on, reference=payment.reference, description=f'Payment to {payment.supplier_bill.purchase_order.supplier.name}', lines=[{'account': accounts[Account.SystemRole.ACCOUNTS_PAYABLE], 'debit': payment.amount}, {'account': accounts[Account.SystemRole.BANK], 'credit': payment.amount}], user=payment.recorded_by)


def post_fulfilment(fulfilment):
    from apps.inventory.models import StockMovement
    movements = StockMovement.objects.filter(source_type='fulfilment', source_id=fulfilment.id)
    cost = sum((movement.quantity * movement.unit_cost for movement in movements), Decimal('0.00')).quantize(Decimal('0.01'))
    if not cost:
        return None
    accounts = system_accounts(Account.SystemRole.INVENTORY, Account.SystemRole.COST_OF_GOODS_SOLD)
    if not accounts:
        return None
    return post_source(source_type='fulfilment', source_id=fulfilment.id, date=fulfilment.fulfilled_on, reference=fulfilment.reference or fulfilment.sales_order.number or '', description=f'Cost of goods sold for {fulfilment.sales_order.number}', lines=[{'account': accounts[Account.SystemRole.COST_OF_GOODS_SOLD], 'debit': cost}, {'account': accounts[Account.SystemRole.INVENTORY], 'credit': cost}], user=fulfilment.fulfilled_by)


def post_payroll_accrual(pay_run):
    roles = [Account.SystemRole.PAYROLL_EXPENSE, Account.SystemRole.PAYROLL_PAYABLE, Account.SystemRole.PAYROLL_TAX_PAYABLE]
    accounts = system_accounts(*roles)
    if not accounts:
        return None
    employer_uif = sum((slip.uif_employer for slip in pay_run.payslips.all()), Decimal('0.00'))
    statutory = pay_run.deductions_total + employer_uif
    expense = pay_run.gross_total + employer_uif
    return post_source(source_type='payroll_accrual', source_id=pay_run.id, date=pay_run.payment_date, reference=f'PAY-{pay_run.id}', description=f'Payroll {pay_run.period_start} to {pay_run.period_end}', lines=[{'account': accounts[Account.SystemRole.PAYROLL_EXPENSE], 'debit': expense}, {'account': accounts[Account.SystemRole.PAYROLL_PAYABLE], 'credit': pay_run.net_total}, {'account': accounts[Account.SystemRole.PAYROLL_TAX_PAYABLE], 'credit': statutory}], user=pay_run.approved_by)


def post_payroll_payment(pay_run, user):
    accounts = system_accounts(Account.SystemRole.BANK, Account.SystemRole.PAYROLL_PAYABLE)
    if not accounts:
        return None
    return post_source(source_type='payroll_payment', source_id=pay_run.id, date=pay_run.payment_date, reference=f'PAY-BANK-{pay_run.id}', description=f'Net payroll payment for {pay_run.period_end}', lines=[{'account': accounts[Account.SystemRole.PAYROLL_PAYABLE], 'debit': pay_run.net_total}, {'account': accounts[Account.SystemRole.BANK], 'credit': pay_run.net_total}], user=user)
