from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.clients.models import Client
from apps.inventory.models import StockLocation, StockMovement
from apps.products.models import Product
from apps.sales.models import SalesOrder


class SalesApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sales-manager', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.customer = Client.objects.create(name='Retail Customer')
        self.location = StockLocation.objects.create(code='SALE', name='Sales stock')
        self.product = Product.objects.create(sku='SALE-1', name='Sellable item', product_type=Product.Type.STOCK, sales_price='100.00')
        StockMovement.objects.create(product=self.product, location=self.location, movement_type='receipt', quantity='10.000', occurred_on=timezone.localdate(), created_by=self.user)

    def test_sales_order_can_invoice_and_fulfil(self):
        order = self.client.post('/api/v1/sales-orders/', {'client': self.customer.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/sales-order-lines/', {'sales_order': order['id'], 'product': self.product.id, 'quantity': '2.000', 'unit_price': '100.00', 'tax_rate': '15.00'}, format='json')
        confirmed = self.client.post(f"/api/v1/sales-orders/{order['id']}/confirm/", {}, format='json')
        self.assertEqual(confirmed.data['number'], 'SO-000001')
        invoice = self.client.post(f"/api/v1/sales-orders/{order['id']}/invoice/", {'due_date': timezone.localdate() + timedelta(days=14)}, format='json')
        self.assertEqual(invoice.status_code, status.HTTP_200_OK)
        self.assertEqual(invoice.data['status'], 'issued')
        fulfilled = self.client.post(f"/api/v1/sales-orders/{order['id']}/fulfil/", {'fulfilled_on': timezone.localdate()}, format='json')
        self.assertEqual(fulfilled.status_code, status.HTTP_200_OK)
        self.assertEqual(StockMovement.objects.filter(source_type='sales_order').get().quantity, 2)

    def test_fulfilment_fails_without_enough_stock(self):
        order = self.client.post('/api/v1/sales-orders/', {'client': self.customer.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/sales-order-lines/', {'sales_order': order['id'], 'product': self.product.id, 'quantity': '11.000', 'unit_price': '100.00'}, format='json')
        self.client.post(f"/api/v1/sales-orders/{order['id']}/confirm/", {}, format='json')
        response = self.client.post(f"/api/v1/sales-orders/{order['id']}/fulfil/", {'fulfilled_on': timezone.localdate()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SalesOrder.objects.get(pk=order['id']).status, SalesOrder.Status.CONFIRMED)

    def test_sales_order_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Sales Orders')
