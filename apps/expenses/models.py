from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Expense categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PAID = 'paid', 'Paid'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        EFT = 'eft', 'EFT'
        OTHER = 'other', 'Other'

    description = models.CharField(max_length=255)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    incurred_on = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(max_length=12, choices=PaymentMethod.choices, default=PaymentMethod.CARD)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submitted_expenses')
    client = models.ForeignKey('clients.Client', null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')
    engagement = models.ForeignKey('engagements.Engagement', null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')
    receipt_document = models.ForeignKey('documents.Document', null=True, blank=True, on_delete=models.SET_NULL, related_name='expense_receipts')
    notes = models.TextField(blank=True)
    paid_on = models.DateField(null=True, blank=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='paid_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-incurred_on', '-id']

    def __str__(self):
        return f'{self.description} — R{self.amount}'


class ExpenseApproval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='approvals')
    decision = models.CharField(max_length=12, choices=Decision.choices)
    comment = models.TextField(blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='expense_decisions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
