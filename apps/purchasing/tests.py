from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.inventory.models import StockLocation, StockMovement
from apps.products.models import Product
from .models import Supplier


class PurchasingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.supplier = Supplier.objects.create(name='Local Supplier')
        self.location = StockLocation.objects.create(code='BUY', name='Receiving')
        self.product = Product.objects.create(sku='BUY-1', name='Purchased item', product_type=Product.Type.STOCK, cost_price='20.00')

    def test_approved_purchase_order_receipt_adds_stock(self):
        order = self.client.post('/api/v1/purchase-orders/', {'supplier': self.supplier.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/purchase-order-lines/', {'purchase_order': order['id'], 'product': self.product.id, 'quantity': '5.000', 'unit_cost': '20.00'}, format='json')
        approved = self.client.post(f"/api/v1/purchase-orders/{order['id']}/approve/", {}, format='json')
        self.assertEqual(approved.data['number'], 'PO-000001')
        received = self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {'received_on': timezone.localdate()}, format='json')
        self.assertEqual(received.status_code, status.HTTP_200_OK)
        self.assertEqual(StockMovement.objects.get(source_type='purchase_order').quantity, 5)
        repeated = self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {'received_on': timezone.localdate()}, format='json')
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchasing_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/purchasing/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Purchase Management')
