from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.clients.models import Client
from apps.expenses.models import ExpenseCategory
from .models import Account, AccountingPeriod, JournalEntry


class AccountingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='accountant', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.bank = Account.objects.create(code='1000', name='Bank', account_type=Account.Type.ASSET)
        self.sales = Account.objects.create(code='4000', name='Sales', account_type=Account.Type.REVENUE)

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
