from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory
from apps.inventory.models import StockLocation
from apps.products.models import Product
from apps.purchasing.models import Supplier
from functionalities.accounting.services import cash_balance
from functionalities.finance.services import get_finance_overview, ledger_actuals
from .models import Account, AccountingPeriod, BankStatement, JournalEntry


class AccountingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='accountant', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.bank = Account.objects.create(code='1000', name='Bank', account_type=Account.Type.ASSET, system_role=Account.SystemRole.BANK)
        self.sales = Account.objects.create(code='4000', name='Sales', account_type=Account.Type.REVENUE)
        self.expense = Account.objects.create(code='5000', name='Expenses', account_type=Account.Type.EXPENSE)

    def test_balanced_journal_can_be_posted(self):
        response = self.client.post('/api/v1/journals/', {'date': timezone.localdate(), 'description': 'Cash sale', 'lines': [{'account': self.bank.id, 'debit': '115.00', 'credit': '0.00'}, {'account': self.sales.id, 'debit': '0.00', 'credit': '115.00'}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        posted = self.client.post(f"/api/v1/journals/{response.data['id']}/post/", {}, format='json')
        self.assertEqual(posted.status_code, status.HTTP_200_OK)
        self.assertEqual(posted.data['status'], JournalEntry.Status.POSTED)
        self.assertEqual(Decimal(posted.data['total_debit']), Decimal('115.00'))

    def test_unbalanced_journal_is_rejected_on_post(self):
        response = self.client.post('/api/v1/journals/', {'date': timezone.localdate(), 'description': 'Invalid', 'lines': [{'account': self.bank.id, 'debit': '100.00', 'credit': '0.00'}, {'account': self.sales.id, 'debit': '0.00', 'credit': '90.00'}]}, format='json')
        posted = self.client.post(f"/api/v1/journals/{response.data['id']}/post/", {}, format='json')
        self.assertEqual(posted.status_code, status.HTTP_400_BAD_REQUEST)

    def test_journal_cannot_overdraw_the_canonical_bank_account(self):
        today = timezone.localdate()
        entry = self.client.post('/api/v1/journals/', {
            'date': today,
            'description': 'Unaffordable payment',
            'lines': [
                {'account': self.expense.id, 'debit': '1.00'},
                {'account': self.bank.id, 'credit': '1.00'},
            ],
        }, format='json').data
        response = self.client.post(f"/api/v1/journals/{entry['id']}/post/", {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient cash', str(response.data))
        self.assertEqual(JournalEntry.objects.get(pk=entry['id']).status, JournalEntry.Status.DRAFT)

    def test_cash_received_funds_a_later_payment(self):
        today = timezone.localdate()
        deposit = self.client.post('/api/v1/journals/', {
            'date': today,
            'description': 'Cash received',
            'lines': [
                {'account': self.bank.id, 'debit': '100.00'},
                {'account': self.sales.id, 'credit': '100.00'},
            ],
        }, format='json').data
        self.client.post(f"/api/v1/journals/{deposit['id']}/post/", {}, format='json')
        payment = self.client.post('/api/v1/journals/', {
            'date': today,
            'description': 'Affordable payment',
            'lines': [
                {'account': self.expense.id, 'debit': '60.00'},
                {'account': self.bank.id, 'credit': '60.00'},
            ],
        }, format='json').data
        response = self.client.post(f"/api/v1/journals/{payment['id']}/post/", {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cash_balance(as_of=today), Decimal('40.00'))

    def test_closed_period_prevents_posting(self):
        today = timezone.localdate()
        AccountingPeriod.objects.create(name='Closed month', start_date=today, end_date=today, is_closed=True)
        entry = self.client.post('/api/v1/journals/', {'date': today, 'description': 'Locked', 'lines': [{'account': self.bank.id, 'debit': '10.00'}, {'account': self.sales.id, 'credit': '10.00'}]}, format='json').data
        response = self.client.post(f"/api/v1/journals/{entry['id']}/post/", {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accounting_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/accounting/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Accounting &amp; Bookkeeping')
        self.assertContains(response, 'Financial statements')
        self.assertContains(response, 'Bank reconciliation')
        self.assertContains(response, 'statementFile')
        self.assertContains(response, 'Download CSV template')
        self.assertContains(response, 'Bank / Cash system role')

    def test_posted_journal_can_be_reversed_once(self):
        today = timezone.localdate()
        entry = self.client.post('/api/v1/journals/', {'date': today, 'reference': 'ORIG', 'description': 'Original', 'lines': [{'account': self.bank.id, 'debit': '50.00'}, {'account': self.sales.id, 'credit': '50.00'}]}, format='json').data
        self.client.post(f"/api/v1/journals/{entry['id']}/post/", {}, format='json')
        reversal = self.client.post(f"/api/v1/journals/{entry['id']}/reverse/", {'date': today}, format='json')
        self.assertEqual(reversal.status_code, status.HTTP_200_OK)
        self.assertEqual(reversal.data['reversal_of'], entry['id'])
        self.assertEqual(JournalEntry.objects.get(pk=entry['id']).status, JournalEntry.Status.REVERSED)
        repeated = self.client.post(f"/api/v1/journals/{entry['id']}/reverse/", {'date': today}, format='json')
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)


class AutomaticPostingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='posting-manager', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.customer = Client.objects.create(name='Posting Customer')
        for code, name, account_type, role in [
            ('1000', 'Bank', Account.Type.ASSET, Account.SystemRole.BANK),
            ('1100', 'Receivables', Account.Type.ASSET, Account.SystemRole.ACCOUNTS_RECEIVABLE),
            ('1200', 'Input VAT', Account.Type.ASSET, Account.SystemRole.INPUT_VAT),
            ('2000', 'Payables', Account.Type.LIABILITY, Account.SystemRole.ACCOUNTS_PAYABLE),
            ('2100', 'Output VAT', Account.Type.LIABILITY, Account.SystemRole.OUTPUT_VAT),
            ('4000', 'Sales', Account.Type.REVENUE, Account.SystemRole.SALES_REVENUE),
            ('5000', 'Expenses', Account.Type.EXPENSE, Account.SystemRole.GENERAL_EXPENSE),
        ]:
            Account.objects.create(code=code, name=name, account_type=account_type, system_role=role)

    def test_invoice_payment_and_expense_post_to_ledger(self):
        today = timezone.localdate()
        invoice = self.client.post('/api/v1/invoices/', {'client': self.customer.id, 'due_date': today}, format='json').data
        self.client.post('/api/v1/invoice-lines/', {'invoice': invoice['id'], 'description': 'Service', 'quantity': '1.00', 'unit_price': '100.00', 'tax_rate': '15.00'}, format='json')
        issued = self.client.post(f"/api/v1/invoices/{invoice['id']}/issue/", {}, format='json')
        self.assertEqual(issued.status_code, status.HTTP_200_OK)
        self.assertTrue(JournalEntry.objects.filter(source_type='invoice', source_id=invoice['id'], status='posted').exists())
        payment = self.client.post('/api/v1/payments/', {'invoice': invoice['id'], 'amount': '115.00', 'paid_on': today}, format='json')
        self.assertEqual(payment.status_code, status.HTTP_201_CREATED)
        self.assertTrue(JournalEntry.objects.filter(source_type='customer_payment', source_id=payment.data['id'], status='posted').exists())
        category = ExpenseCategory.objects.create(name='Posting expense')
        expense = self.client.post('/api/v1/expenses/', {'description': 'Office cost', 'category': category.id, 'amount': '115.00', 'vat_amount': '15.00'}, format='json').data
        self.client.post(f"/api/v1/expenses/{expense['id']}/submit/", {}, format='json')
        approved = self.client.post(f"/api/v1/expenses/{expense['id']}/approve/", {}, format='json')
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        self.assertTrue(JournalEntry.objects.filter(source_type='expense', source_id=expense['id'], status='posted').exists())

    def test_expense_payment_rolls_back_when_cash_is_insufficient(self):
        today = timezone.localdate()
        category = ExpenseCategory.objects.create(name='Cash guard expense')
        expense = self.client.post('/api/v1/expenses/', {
            'description': 'Unaffordable cost',
            'category': category.id,
            'amount': '50.00',
        }, format='json').data
        self.client.post(f"/api/v1/expenses/{expense['id']}/submit/", {}, format='json')
        self.client.post(f"/api/v1/expenses/{expense['id']}/approve/", {}, format='json')

        response = self.client.post(f"/api/v1/expenses/{expense['id']}/pay/", {'paid_on': today}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient cash', str(response.data))
        self.assertEqual(Expense.objects.get(pk=expense['id']).status, Expense.Status.APPROVED)
        self.assertFalse(JournalEntry.objects.filter(source_type='expense_payment', source_id=expense['id']).exists())


class CanonicalFinancialIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='canonical-ceo', password='test-pass-123', role=User.Role.CEO)
        self.client.force_authenticate(self.user)
        self.customer = Client.objects.create(name='Canonical Customer')
        self.location = StockLocation.objects.create(code='CANON', name='Canonical stock')
        self.product = Product.objects.create(sku='CANON-1', name='Canonical item', product_type=Product.Type.STOCK, sales_price='100.00', cost_price='60.00')
        self.supplier = Supplier.objects.create(name='Canonical Supplier')
        accounts = [
            ('1000', 'Bank', Account.Type.ASSET, Account.SystemRole.BANK),
            ('1100', 'Receivables', Account.Type.ASSET, Account.SystemRole.ACCOUNTS_RECEIVABLE),
            ('1200', 'Input VAT', Account.Type.ASSET, Account.SystemRole.INPUT_VAT),
            ('1300', 'Inventory', Account.Type.ASSET, Account.SystemRole.INVENTORY),
            ('2000', 'Payables', Account.Type.LIABILITY, Account.SystemRole.ACCOUNTS_PAYABLE),
            ('2100', 'Output VAT', Account.Type.LIABILITY, Account.SystemRole.OUTPUT_VAT),
            ('2200', 'Payroll payable', Account.Type.LIABILITY, Account.SystemRole.PAYROLL_PAYABLE),
            ('2300', 'Payroll deductions', Account.Type.LIABILITY, Account.SystemRole.PAYROLL_TAX_PAYABLE),
            ('4000', 'Sales', Account.Type.REVENUE, Account.SystemRole.SALES_REVENUE),
            ('5000', 'General expenses', Account.Type.EXPENSE, Account.SystemRole.GENERAL_EXPENSE),
            ('5100', 'Cost of goods sold', Account.Type.EXPENSE, Account.SystemRole.COST_OF_GOODS_SOLD),
            ('5200', 'Payroll expense', Account.Type.EXPENSE, Account.SystemRole.PAYROLL_EXPENSE),
        ]
        for code, name, account_type, role in accounts:
            Account.objects.create(code=code, name=name, account_type=account_type, system_role=role)
        self.capital = Account.objects.create(code='3000', name='Opening capital', account_type=Account.Type.EQUITY)

    def test_buy_sell_expense_and_payroll_share_one_ledger(self):
        today = timezone.localdate()

        opening_cash = self.client.post('/api/v1/journals/', {
            'date': today,
            'reference': 'OPENING-CASH',
            'description': 'Opening cash balance',
            'lines': [
                {'account': Account.objects.get(system_role=Account.SystemRole.BANK).id, 'debit': '2000.00'},
                {'account': self.capital.id, 'credit': '2000.00'},
            ],
        }, format='json').data
        self.client.post(f"/api/v1/journals/{opening_cash['id']}/post/", {}, format='json')

        order = self.client.post('/api/v1/purchase-orders/', {'supplier': self.supplier.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/purchase-order-lines/', {'purchase_order': order['id'], 'product': self.product.id, 'quantity': '2.000', 'unit_cost': '60.00', 'tax_rate': '15.00'}, format='json')
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/approve/", {}, format='json')
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {}, format='json')
        bill = self.client.post(f"/api/v1/purchase-orders/{order['id']}/create-bill/", {'supplier_invoice_number': 'CAN-1', 'bill_date': today, 'due_date': today}, format='json').data
        self.client.post(f"/api/v1/supplier-bills/{bill['id']}/post/", {}, format='json')
        supplier_payment = self.client.post(f"/api/v1/supplier-bills/{bill['id']}/pay/", {'amount': '138.00', 'paid_on': today}, format='json')
        self.assertEqual(supplier_payment.status_code, status.HTTP_200_OK)

        sale = self.client.post('/api/v1/sales-orders/', {'client': self.customer.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/sales-order-lines/', {'sales_order': sale['id'], 'product': self.product.id, 'quantity': '1.000', 'unit_price': '100.00', 'tax_rate': '15.00'}, format='json')
        self.client.post(f"/api/v1/sales-orders/{sale['id']}/confirm/", {}, format='json')
        invoice = self.client.post(f"/api/v1/sales-orders/{sale['id']}/invoice/", {'due_date': today}, format='json').data
        self.client.post(f"/api/v1/sales-orders/{sale['id']}/fulfil/", {'fulfilled_on': today}, format='json')
        self.client.post('/api/v1/payments/', {'invoice': invoice['id'], 'amount': '115.00', 'paid_on': today}, format='json')

        category = ExpenseCategory.objects.create(name='Canonical expense')
        expense = self.client.post('/api/v1/expenses/', {'description': 'Operations', 'category': category.id, 'amount': '23.00', 'vat_amount': '3.00'}, format='json').data
        self.client.post(f"/api/v1/expenses/{expense['id']}/submit/", {}, format='json')
        self.client.post(f"/api/v1/expenses/{expense['id']}/approve/", {}, format='json')
        paid_expense = self.client.post(f"/api/v1/expenses/{expense['id']}/pay/", {'paid_on': today}, format='json')
        self.assertEqual(paid_expense.data['status'], 'paid')

        staff = User.objects.create_user(username='canonical-staff', role=User.Role.STAFF)
        employee = self.client.post('/api/v1/payroll-employees/', {'user': staff.id, 'employee_number': 'CAN-E1', 'monthly_basic': '1000.00'}, format='json').data
        pay_run = self.client.post('/api/v1/pay-runs/', {'period_start': today.replace(day=1), 'period_end': today, 'payment_date': today, 'initial_payslip': {'employee': employee['id'], 'basic_salary': '1000.00', 'paye': '100.00', 'uif_employee': '10.00', 'uif_employer': '10.00'}}, format='json').data
        self.client.post(f"/api/v1/pay-runs/{pay_run['id']}/approve/", {}, format='json')
        self.client.post(f"/api/v1/pay-runs/{pay_run['id']}/mark-paid/", {}, format='json')

        actuals = ledger_actuals()
        self.assertEqual(actuals['revenue'], Decimal('100.00'))
        self.assertEqual(actuals['expenses'], Decimal('1090.00'))
        self.assertEqual(actuals['net_profit'], Decimal('-990.00'))
        overview = get_finance_overview()
        self.assertEqual(overview['total_revenue'], actuals['revenue'])
        self.assertEqual(overview['total_expenses'], actuals['expenses'])
        self.assertEqual(overview['net_profit'], actuals['net_profit'])
        for source_type in ('supplier_bill', 'supplier_payment', 'invoice', 'customer_payment', 'fulfilment', 'expense', 'expense_payment', 'payroll_accrual', 'payroll_payment'):
            self.assertTrue(JournalEntry.objects.filter(source_type=source_type, status=JournalEntry.Status.POSTED).exists(), source_type)


class FinancialReportingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='report-user', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.bank = Account.objects.create(code='1000', name='Bank', account_type=Account.Type.ASSET)
        self.equity = Account.objects.create(code='3000', name='Capital', account_type=Account.Type.EQUITY)
        self.sales = Account.objects.create(code='4000', name='Sales', account_type=Account.Type.REVENUE)
        self.expense = Account.objects.create(code='5000', name='Operating costs', account_type=Account.Type.EXPENSE)

    def post_journal(self, lines, reference):
        entry = self.client.post('/api/v1/journals/', {'date': timezone.localdate(), 'reference': reference, 'description': reference, 'lines': lines}, format='json').data
        return self.client.post(f"/api/v1/journals/{entry['id']}/post/", {}, format='json')

    def test_trial_balance_income_statement_and_balance_sheet(self):
        self.post_journal([{'account': self.bank.id, 'debit': '1000.00'}, {'account': self.equity.id, 'credit': '1000.00'}], 'CAPITAL')
        self.post_journal([{'account': self.bank.id, 'debit': '230.00'}, {'account': self.sales.id, 'credit': '230.00'}], 'SALE')
        self.post_journal([{'account': self.expense.id, 'debit': '30.00'}, {'account': self.bank.id, 'credit': '30.00'}], 'COST')
        today = timezone.localdate().isoformat()

        trial = self.client.get('/api/v1/accounting/reports/trial-balance/', {'as_of': today})
        self.assertEqual(trial.status_code, status.HTTP_200_OK)
        self.assertTrue(trial.data['is_balanced'])
        self.assertEqual(Decimal(trial.data['total_debit']), Decimal('1230.00'))

        income = self.client.get('/api/v1/accounting/reports/income-statement/', {'start_date': today, 'end_date': today})
        self.assertEqual(Decimal(income.data['net_profit']), Decimal('200.00'))

        balance = self.client.get('/api/v1/accounting/reports/balance-sheet/', {'as_of': today})
        self.assertTrue(balance.data['is_balanced'])
        self.assertEqual(Decimal(balance.data['total_assets']), Decimal('1200.00'))
        self.assertEqual(Decimal(balance.data['total_equity']), Decimal('1200.00'))

    def test_report_rejects_invalid_date_range(self):
        response = self.client.get('/api/v1/accounting/reports/income-statement/', {'start_date': '2026-08-02', 'end_date': '2026-08-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BankReconciliationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reconcile-user', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.bank = Account.objects.create(code='1000', name='Bank', account_type=Account.Type.ASSET, system_role=Account.SystemRole.BANK)
        self.sales = Account.objects.create(code='4000', name='Sales', account_type=Account.Type.REVENUE)
        today = timezone.localdate()
        entry = self.client.post('/api/v1/journals/', {'date': today, 'reference': 'DEP-100', 'description': 'Deposit', 'lines': [{'account': self.bank.id, 'debit': '100.00'}, {'account': self.sales.id, 'credit': '100.00'}]}, format='json').data
        self.client.post(f"/api/v1/journals/{entry['id']}/post/", {}, format='json')
        self.today = today

    def test_statement_import_candidate_and_reconciliation(self):
        response = self.client.post('/api/v1/bank-statements/', {
            'bank_account': self.bank.id,
            'reference': 'AUG-2026',
            'start_date': self.today,
            'end_date': self.today,
            'opening_balance': '0.00',
            'closing_balance': '100.00',
            'lines': [{'transaction_date': self.today, 'description': 'Customer deposit', 'reference': 'DEP-100', 'amount': '100.00'}],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        line_id = response.data['statement_lines'][0]['id']
        candidates = self.client.get(f'/api/v1/bank-statement-lines/{line_id}/candidates/')
        self.assertEqual(candidates.status_code, status.HTTP_200_OK)
        self.assertEqual(len(candidates.data), 1)
        invalid_match = self.client.post(f'/api/v1/bank-statement-lines/{line_id}/reconcile/', {'journal_line': 'invalid'}, format='json')
        self.assertEqual(invalid_match.status_code, status.HTTP_400_BAD_REQUEST)
        matched = self.client.post(f'/api/v1/bank-statement-lines/{line_id}/reconcile/', {'journal_line': candidates.data[0]['id']}, format='json')
        self.assertEqual(matched.status_code, status.HTTP_200_OK)
        self.assertTrue(matched.data['is_reconciled'])
        self.assertEqual(BankStatement.objects.get(pk=response.data['id']).status, BankStatement.Status.RECONCILED)

        unmatched = self.client.post(f'/api/v1/bank-statement-lines/{line_id}/unreconcile/', {}, format='json')
        self.assertEqual(unmatched.status_code, status.HTTP_200_OK)
        self.assertEqual(BankStatement.objects.get(pk=response.data['id']).status, BankStatement.Status.OPEN)

    def test_statement_totals_must_reconcile(self):
        response = self.client.post('/api/v1/bank-statements/', {'bank_account': self.bank.id, 'reference': 'BAD', 'start_date': self.today, 'end_date': self.today, 'opening_balance': '0.00', 'closing_balance': '90.00', 'lines': [{'transaction_date': self.today, 'description': 'Deposit', 'amount': '100.00'}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
