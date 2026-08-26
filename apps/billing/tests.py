from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.clients.models import Client
from .models import Invoice


class BillingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='billing', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.customer = Client.objects.create(name='Acme SME')

    def test_invoice_issue_and_partial_payment_workflow(self):
        today = timezone.localdate()
        created = self.client.post('/api/invoices/', {'client': self.customer.id, 'issue_date': today, 'due_date': today + timedelta(days=14)}, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        invoice_id = created.data['id']
        line = self.client.post('/api/invoice-lines/', {'invoice': invoice_id, 'description': 'Consulting', 'quantity': '2.00', 'unit_price': '1000.00', 'tax_rate': '15.00'}, format='json')
        self.assertEqual(line.status_code, status.HTTP_201_CREATED)
        issued = self.client.post(f'/api/invoices/{invoice_id}/issue/', {}, format='json')
        self.assertEqual(issued.status_code, status.HTTP_200_OK)
        self.assertEqual(issued.data['number'], 'INV-000001')
        self.assertEqual(Decimal(issued.data['total']), Decimal('2300.00'))
        payment = self.client.post('/api/payments/', {'invoice': invoice_id, 'amount': '300.00', 'paid_on': today}, format='json')
        self.assertEqual(payment.status_code, status.HTTP_201_CREATED)
        invoice = Invoice.objects.get(pk=invoice_id)
        self.assertEqual(invoice.status, Invoice.Status.PART_PAID)
        self.assertEqual(invoice.balance_due, Decimal('2000.00'))

    def test_cannot_issue_empty_invoice(self):
        today = timezone.localdate()
        created = self.client.post('/api/invoices/', {'client': self.customer.id, 'due_date': today}, format='json')
        response = self.client.post(f"/api/invoices/{created.data['id']}/issue/", {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regular_staff_cannot_create_invoice(self):
        staff = User.objects.create_user(username='billing-staff', password='test-pass-123')
        self.client.force_authenticate(staff)
        response = self.client.post('/api/invoices/', {'client': self.customer.id, 'due_date': timezone.localdate()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_cannot_exceed_balance(self):
        today = timezone.localdate()
        invoice = self.client.post('/api/invoices/', {'client': self.customer.id, 'due_date': today}, format='json').data
        self.client.post('/api/invoice-lines/', {'invoice': invoice['id'], 'description': 'Service', 'quantity': '1.00', 'unit_price': '100.00', 'tax_rate': '0.00'}, format='json')
        self.client.post(f"/api/invoices/{invoice['id']}/issue/", {}, format='json')
        response = self.client.post('/api/payments/', {'invoice': invoice['id'], 'amount': '101.00', 'paid_on': today}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_issued_invoice_cannot_be_deleted(self):
        today = timezone.localdate()
        invoice = self.client.post('/api/invoices/', {'client': self.customer.id, 'due_date': today}, format='json').data
        self.client.post('/api/invoice-lines/', {'invoice': invoice['id'], 'description': 'Service', 'quantity': '1.00', 'unit_price': '100.00'}, format='json')
        self.client.post(f"/api/invoices/{invoice['id']}/issue/", {}, format='json')
        response = self.client.delete(f"/api/invoices/{invoice['id']}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
