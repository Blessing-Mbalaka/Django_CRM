from apps.companies.models import CompanyOwnedModel
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class NumberSequence(CompanyOwnedModel):
    key = models.CharField(max_length=40)
    prefix = models.CharField(max_length=20, default='INV')
    next_number = models.PositiveBigIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'key'], name='billing_numbersequence_key_company')]


class Invoice(CompanyOwnedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        PART_PAID = 'part_paid', 'Part Paid'
        PAID = 'paid', 'Paid'
        VOID = 'void', 'Void'

    number = models.CharField(max_length=40, null=True, blank=True)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='invoices')
    engagement = models.ForeignKey('engagements.Engagement', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    currency = models.CharField(max_length=3, default='ZAR')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'number'], name='billing_invoice_number_company')]
        ordering = ['-issue_date', '-id']

    @property
    def subtotal(self):
        return sum((line.net_amount for line in self.lines.all()), Decimal('0.00'))

    @property
    def tax_total(self):
        return sum((line.tax_amount for line in self.lines.all()), Decimal('0.00'))

    @property
    def total(self):
        return self.subtotal + self.tax_total

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @property
    def balance_due(self):
        return max(self.total - self.amount_paid, Decimal('0.00'))

    def __str__(self):
        return self.number or f'Draft invoice {self.pk}'


class InvoiceLine(CompanyOwnedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), validators=[MinValueValidator(Decimal('0.00'))])
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    @property
    def net_amount(self):
        return (self.quantity * self.unit_price).quantize(Decimal('0.01'))

    @property
    def tax_amount(self):
        return (self.net_amount * self.tax_rate / Decimal('100')).quantize(Decimal('0.01'))


class Payment(CompanyOwnedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    paid_on = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=120, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-id']

