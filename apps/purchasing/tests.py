from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounting.models import Account, JournalEntry
from apps.inventory.models import StockLocation, StockMovement
from apps.products.models import Product
from .models import Supplier


class SupplierInventoryMetadataTests(TestCase):
    def test_optional_inventory_metadata_preserves_supplier(self):
        supplier = Supplier.objects.create(name='Metadata Supplier', contact_person='A Person', address='1 Main Road', notes='Preferred')
        supplier.refresh_from_db()
        self.assertEqual(supplier.contact_person, 'A Person')
        self.assertEqual(supplier.address, '1 Main Road')
        self.assertEqual(supplier.notes, 'Preferred')


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
        self.assertEqual(StockMovement.objects.get(source_type='goods_receipt').quantity, 5)
        repeated = self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {'received_on': timezone.localdate()}, format='json')
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchasing_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/purchasing/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Purchase Management')

    def test_partial_receipts_accumulate_without_over_receipt(self):
        order = self.client.post('/api/v1/purchase-orders/', {'supplier': self.supplier.id, 'location': self.location.id}, format='json').data
        line = self.client.post('/api/v1/purchase-order-lines/', {'purchase_order': order['id'], 'product': self.product.id, 'quantity': '5.000', 'unit_cost': '20.00'}, format='json').data
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/approve/", {}, format='json')
        first = self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {'lines': [{'line': line['id'], 'quantity': '2.000'}]}, format='json')
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(str(first.data['lines'][0]['quantity']), '2.000')
        order_state = self.client.get(f"/api/v1/purchase-orders/{order['id']}/").data
        self.assertEqual(order_state['status'], 'part_received')
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {'lines': [{'line': line['id'], 'quantity': '3.000'}]}, format='json')
        order_state = self.client.get(f"/api/v1/purchase-orders/{order['id']}/").data
        self.assertEqual(order_state['status'], 'received')

    def test_received_order_can_create_and_post_supplier_bill(self):
        for code, name, account_type, role in [
            ('1200', 'Input VAT', Account.Type.ASSET, Account.SystemRole.INPUT_VAT),
            ('1300', 'Inventory', Account.Type.ASSET, Account.SystemRole.INVENTORY),
            ('2000', 'Payables', Account.Type.LIABILITY, Account.SystemRole.ACCOUNTS_PAYABLE),
        ]:
            Account.objects.create(code=code, name=name, account_type=account_type, system_role=role)
        today = timezone.localdate()
        order = self.client.post('/api/v1/purchase-orders/', {'supplier': self.supplier.id, 'location': self.location.id}, format='json').data
        self.client.post('/api/v1/purchase-order-lines/', {'purchase_order': order['id'], 'product': self.product.id, 'quantity': '2.000', 'unit_cost': '100.00', 'tax_rate': '15.00'}, format='json')
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/approve/", {}, format='json')
        self.client.post(f"/api/v1/purchase-orders/{order['id']}/receive/", {}, format='json')
        bill = self.client.post(f"/api/v1/purchase-orders/{order['id']}/create-bill/", {'supplier_invoice_number': 'SUP-001', 'bill_date': today, 'due_date': today}, format='json')
        self.assertEqual(bill.status_code, status.HTTP_200_OK)
        posted = self.client.post(f"/api/v1/supplier-bills/{bill.data['id']}/post/", {}, format='json')
        self.assertEqual(posted.status_code, status.HTTP_200_OK)
        self.assertEqual(posted.data['status'], 'posted')
        self.assertTrue(JournalEntry.objects.filter(source_type='supplier_bill', source_id=bill.data['id'], status='posted').exists())
