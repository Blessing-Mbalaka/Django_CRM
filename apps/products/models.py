from apps.companies.models import CompanyOwnedModel
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(CompanyOwnedModel):
    class Type(models.TextChoices):
        STOCK = 'stock', 'Stock item'
        SERVICE = 'service', 'Service'

    sku = models.CharField(max_length=60)
    name = models.CharField(max_length=180)
    product_type = models.CharField(max_length=10, choices=Type.choices, default=Type.STOCK)
    description = models.TextField(blank=True)
    sales_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'sku'], name='products_product_sku_company')]
        ordering = ['name']

    def __str__(self):
        return f'{self.sku} · {self.name}'

