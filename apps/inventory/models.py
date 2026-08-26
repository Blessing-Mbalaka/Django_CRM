from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class StockLocation(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=140)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    class Type(models.TextChoices):
        RECEIPT = 'receipt', 'Receipt'
        ISSUE = 'issue', 'Issue'
        ADJUSTMENT_IN = 'adjustment_in', 'Positive adjustment'
        ADJUSTMENT_OUT = 'adjustment_out', 'Negative adjustment'

    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='stock_movements')
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=Type.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    reference = models.CharField(max_length=100, blank=True)
    source_type = models.CharField(max_length=40, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    occurred_on = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_on', '-id']

    @property
    def signed_quantity(self):
        if self.movement_type in (self.Type.ISSUE, self.Type.ADJUSTMENT_OUT):
            return -self.quantity
        return self.quantity


class ReorderRule(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reorder_rules')
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name='reorder_rules')
    minimum_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'location'], name='inventory_unique_reorder_rule')]

