from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=180)
    contact_person = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tax_number = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseSequence(models.Model):
    key = models.CharField(max_length=30, unique=True, default='purchase_order')
    prefix = models.CharField(max_length=15, default='PO')
    next_number = models.PositiveBigIntegerField(default=1)


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        APPROVED = 'approved', 'Approved'
        PART_RECEIVED = 'part_received', 'Part Received'
        RECEIVED = 'received', 'Received'
        CANCELLED = 'cancelled', 'Cancelled'

    number = models.CharField(max_length=40, unique=True, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    location = models.ForeignKey('inventory.StockLocation', on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField(default=timezone.localdate)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']

    @property
    def total(self):
        return sum((line.line_total for line in self.lines.all()), Decimal('0.00'))


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='purchase_order_lines')
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))
    received_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    @property
    def line_total(self):
        return (self.quantity * self.unit_cost).quantize(Decimal('0.01'))


class GoodsReceipt(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receipts')
    received_on = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='goods_receipts')
    created_at = models.DateTimeField(auto_now_add=True)


class GoodsReceiptLine(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='lines')
    purchase_order_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT, related_name='receipt_lines')
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])


class SupplierBill(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        POSTED = 'posted', 'Posted'
        PART_PAID = 'part_paid', 'Part Paid'
        PAID = 'paid', 'Paid'

    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.PROTECT, related_name='supplier_bill')
    supplier_invoice_number = models.CharField(max_length=80)
    bill_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=16, decimal_places=2)
    tax_total = models.DecimalField(max_digits=16, decimal_places=2)
    total = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.OneToOneField('accounting.JournalEntry', null=True, blank=True, on_delete=models.PROTECT, related_name='supplier_bill')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_supplier_bills')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bill_date', '-id']
        constraints = [models.UniqueConstraint(fields=['purchase_order', 'supplier_invoice_number'], name='purchasing_unique_supplier_bill_number')]

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    @property
    def balance_due(self):
        return max(self.total - self.amount_paid, Decimal('0.00'))


class SupplierPayment(models.Model):
    supplier_bill = models.ForeignKey(SupplierBill, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    paid_on = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=120, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_supplier_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-id']
