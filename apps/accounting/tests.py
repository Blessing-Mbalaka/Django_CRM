from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
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
