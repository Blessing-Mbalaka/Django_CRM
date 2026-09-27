from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.products.models import Product
from functionalities.inventory.queries import inventory_summary, low_stock_rows, product_stock_rows
from functionalities.inventory.reports import report_dataset, safe_csv_cell
from functionalities.inventory.services import record_movement
from .models import InventoryCategory, InventorySettings, ProductInventoryProfile, ReorderRule, StockLocation


class InventoryMetadataTests(TestCase):
    def test_singleton_settings_have_deterministic_defaults(self):
        first = InventorySettings.load()
        second = InventorySettings.load()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.default_unit, 'units')
        self.assertEqual(str(first.default_reorder_level), '0.000')

    def test_category_names_are_case_insensitively_unique(self):
        InventoryCategory.objects.create(name='Equipment')
        with self.assertRaises(Exception):
            InventoryCategory.objects.create(name='equipment')

    def test_profile_defaults_and_assigned_category_protection(self):
        product = Product.objects.create(sku='META-1', name='Existing product')
        category = InventoryCategory.objects.create(name='Materials')
        profile = ProductInventoryProfile.objects.create(product=product, category=category)
        self.assertEqual(profile.unit, 'units')
        with self.assertRaises(ProtectedError):
            category.delete()


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='service-stock', password='test-pass-123')
        self.product = Product.objects.create(sku='SERVICE-1', name='Service stock', product_type=Product.Type.STOCK, cost_price='12.50')
        self.location = StockLocation.objects.create(code='SVC', name='Service location')

    def test_sequential_issues_cannot_overdraw_stock(self):
        common = {'product': self.product, 'location': self.location, 'occurred_on': timezone.localdate(), 'user': self.user}
        record_movement(movement_type='receipt', quantity='5', **common)
        record_movement(movement_type='issue', quantity='4', **common)
        with self.assertRaises(Exception):
            record_movement(movement_type='issue', quantity='2', **common)


class InventoryQueryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='query-stock', password='test-pass-123')
        self.product = Product.objects.create(sku='QUERY-1', name='Query stock', product_type=Product.Type.STOCK, cost_price='10.00')
        self.location = StockLocation.objects.create(code='QUERY', name='Query location')

    def test_existing_product_uses_defaults_and_stock_is_not_duplicated(self):
        InventorySettings.objects.create(default_unit='items', default_reorder_level='3')
        record_movement(product=self.product, location=self.location, movement_type='receipt', quantity='2', occurred_on=timezone.localdate(), user=self.user)
        rows = product_stock_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['unit'], 'items')
        self.assertEqual(rows[0]['status'], 'Low Stock')
        self.assertEqual(rows[0]['inventory_value'], 20)
        self.assertEqual(low_stock_rows()[0]['id'], self.product.id)

    def test_mixed_units_are_labelled_as_aggregate(self):
        other = Product.objects.create(sku='QUERY-2', name='Other stock', product_type=Product.Type.STOCK)
        ProductInventoryProfile.objects.create(product=self.product, unit='kg')
        ProductInventoryProfile.objects.create(product=other, unit='boxes')
        for product in (self.product, other):
            record_movement(product=product, location=self.location, movement_type='receipt', quantity='1', occurred_on=timezone.localdate(), user=self.user)
        self.assertEqual(inventory_summary()['quantity_label'], 'Aggregate quantity')


class InventoryReportTests(InventoryQueryTests):
    def test_exact_report_set_and_safe_csv_cells(self):
        for name in ('Current Stock Summary', 'Inventory Value', 'Low Stock Report', 'Out of Stock Report', 'Stock Movement Summary', 'Products by Category'):
            self.assertEqual(report_dataset(name)['name'], name)
        self.assertEqual(safe_csv_cell('=HYPERLINK("bad")'), "'=HYPERLINK(\"bad\")")


class InventoryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='stock-manager', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(sku='WIDGET-1', name='Widget', product_type=Product.Type.STOCK)
        self.location = StockLocation.objects.create(code='MAIN', name='Main warehouse')

    def test_stock_cannot_go_negative(self):
        response = self.client.post('/api/v1/stock-movements/', {'product': self.product.id, 'location': self.location.id, 'movement_type': 'issue', 'quantity': '1.000', 'occurred_on': timezone.localdate()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_receipt_then_issue_is_recorded(self):
        for movement_type, quantity in [('receipt', '10.000'), ('issue', '3.000')]:
            response = self.client.post('/api/v1/stock-movements/', {'product': self.product.id, 'location': self.location.id, 'movement_type': movement_type, 'quantity': quantity, 'occurred_on': timezone.localdate()}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(f'/api/v1/stock-movements/?product={self.product.id}')
        self.assertEqual(response.data['count'], 2)

    def test_inventory_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Inventory Management')
