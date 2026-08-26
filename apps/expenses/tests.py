from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Expense, ExpenseCategory


class ExpenseApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='expense-staff', password='test-pass-123')
        self.manager = User.objects.create_user(username='expense-manager', password='test-pass-123', role=User.Role.DIRECTOR)
        self.category = ExpenseCategory.objects.create(name='Travel')
        self.client.force_authenticate(self.staff)

    def test_submit_and_manager_approve_workflow(self):
        created = self.client.post('/api/expenses/', {'description': 'Client visit', 'category': self.category.id, 'amount': '575.00', 'vat_amount': '75.00', 'payment_method': 'card'}, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        expense_id = created.data['id']
        submitted = self.client.post(f'/api/expenses/{expense_id}/submit/', {}, format='json')
        self.assertEqual(submitted.data['status'], Expense.Status.SUBMITTED)
        denied = self.client.post(f'/api/expenses/{expense_id}/approve/', {}, format='json')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.manager)
        approved = self.client.post(f'/api/expenses/{expense_id}/approve/', {'comment': 'Receipt checked'}, format='json')
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        self.assertEqual(approved.data['status'], Expense.Status.APPROVED)

    def test_vat_cannot_exceed_expense_amount(self):
        response = self.client.post('/api/expenses/', {'description': 'Invalid', 'category': self.category.id, 'amount': '10.00', 'vat_amount': '15.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submitted_expense_cannot_be_deleted(self):
        created = self.client.post('/api/expenses/', {'description': 'Protected', 'category': self.category.id, 'amount': '100.00'}, format='json').data
        self.client.post(f"/api/expenses/{created['id']}/submit/", {}, format='json')
        response = self.client.delete(f"/api/expenses/{created['id']}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
