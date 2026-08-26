from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class SalesSequence(models.Model):
    key = models.CharField(max_length=30, unique=True, default='sales_order')
    prefix = models.CharField(max_length=15, default='SO')
    next_number = models.PositiveBigIntegerField(default=1)


class SalesOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        FULFILLED = 'fulfilled', 'Fulfilled'
        CANCELLED = 'cancelled', 'Cancelled'

    number = models.CharField(max_length=40, unique=True, null=True, blank=True)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='sales_orders')
    engagement = models.ForeignKey('engagements.Engagement', null=True, blank=True, on_delete=models.SET_NULL, related_name='sales_orders')
    location = models.ForeignKey('inventory.StockLocation', null=True, blank=True, on_delete=models.PROTECT, related_name='sales_orders')
    invoice = models.OneToOneField('billing.Invoice', null=True, blank=True, on_delete=models.SET_NULL, related_name='sales_order')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_sales_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']

    @property
    def subtotal(self):
        return sum((line.net_amount for line in self.lines.all()), Decimal('0.00'))

    @property
    def tax_total(self):
        return sum((line.tax_amount for line in self.lines.all()), Decimal('0.00'))

    @property
    def total(self):
        return self.subtotal + self.tax_total


class SalesOrderLine(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='sales_order_lines')
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))

    @property
    def net_amount(self):
        return (self.quantity * self.unit_price).quantize(Decimal('0.01'))

    @property
    def tax_amount(self):
        return (self.net_amount * self.tax_rate / Decimal('100')).quantize(Decimal('0.01'))


class Fulfilment(models.Model):
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.PROTECT, related_name='fulfilment')
    fulfilled_on = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=100, blank=True)
    fulfilled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales_fulfilments')
    created_at = models.DateTimeField(auto_now_add=True)

