from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.products.models import Product
from .models import InventoryCategory, InventorySettings, ProductInventoryProfile, StockLocation


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
