from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounting.models import Account, JournalEntry, JournalLine
from apps.inventory.models import StockLocation, StockMovement
from apps.products.models import Product
from apps.purchasing.models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, Supplier, SupplierBill


class BusinessActivityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='activity-user', password='test-pass-123', role=User.Role.DIRECTOR)
        self.client.force_authenticate(self.user)
        today = timezone.localdate()
        bank = Account.objects.create(code='A100', name='Bank', account_type=Account.Type.ASSET, system_role=Account.SystemRole.BANK)
        sales = Account.objects.create(code='R400', name='Sales', account_type=Account.Type.REVENUE, system_role=Account.SystemRole.SALES_REVENUE)
        expense = Account.objects.create(code='E500', name='Expenses', account_type=Account.Type.EXPENSE, system_role=Account.SystemRole.GENERAL_EXPENSE)
        for reference, source_type, source_id, lines in (
            ('SALE', 'invoice', 1, ((bank, '100.00', '0.00'), (sales, '0.00', '100.00'))),
            ('COST', 'expense', 2, ((expense, '20.00', '0.00'), (bank, '0.00', '20.00'))),
        ):
            entry = JournalEntry.objects.create(date=today, reference=reference, description=reference, status=JournalEntry.Status.POSTED, source_type=source_type, source_id=source_id, created_by=self.user, posted_at=timezone.now())
            for account, debit, credit in lines:
                JournalLine.objects.create(entry=entry, account=account, debit=debit, credit=credit)

        self.location = StockLocation.objects.create(code='ACT', name='Activity warehouse')
        self.product = Product.objects.create(sku='ACT-1', name='Activity item', product_type=Product.Type.STOCK, cost_price='10.00')
        StockMovement.objects.create(product=self.product, location=self.location, movement_type=StockMovement.Type.RECEIPT, quantity='5.000', unit_cost='10.00', occurred_on=today, created_by=self.user)
        supplier = Supplier.objects.create(name='Activity supplier')
        order = PurchaseOrder.objects.create(supplier=supplier, location=self.location, status=PurchaseOrder.Status.RECEIVED, created_by=self.user)
        order_line = PurchaseOrderLine.objects.create(purchase_order=order, product=self.product, quantity='5.000', unit_cost='10.00', received_quantity='5.000')
        receipt = GoodsReceipt.objects.create(purchase_order=order, received_on=today, received_by=self.user)
        GoodsReceiptLine.objects.create(receipt=receipt, purchase_order_line=order_line, quantity='5.000')
        SupplierBill.objects.create(purchase_order=order, supplier_invoice_number='ACT-BILL', bill_date=today, due_date=today, subtotal='50.00', tax_total='7.50', total='57.50', status=SupplierBill.Status.POSTED, created_by=self.user)

    def test_combined_activity_endpoint_uses_canonical_sources(self):
        today = timezone.localdate().isoformat()
        response = self.client.get('/api/v1/analytics/business-activity/', {'start_date': today, 'end_date': today, 'granularity': 'day'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['revenue'], 100.0)
        self.assertEqual(response.data['summary']['expenses'], 20.0)
        self.assertEqual(response.data['summary']['net_profit'], 80.0)
        self.assertEqual(response.data['summary']['inventory_level'], 5.0)
        self.assertEqual(response.data['summary']['inventory_value'], 50.0)
        self.assertEqual(response.data['summary']['purchasing'], 57.5)
        self.assertEqual(response.data['quantity']['purchase_receipts'], [5.0])

    def test_activity_filters_validate_and_chart_page_renders(self):
        invalid = self.client.get('/api/v1/analytics/business-activity/', {'start_date': '2026-02-02', 'end_date': '2026-01-01'})
        self.assertEqual(invalid.status_code, 400)
        self.client.force_login(self.user)
        page = self.client.get('/analytics/')
        self.assertContains(page, 'Combined Business Activity')
        self.assertContains(page, 'plotly-2.35.2.min.js')
        self.assertContains(page, 'business-activity.js')
