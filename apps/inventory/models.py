from apps.companies.models import CompanyOwnedModel
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class InventoryCategory(CompanyOwnedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(Lower('name'), models.F('company'), name='inventory_category_name_ci_unique')]

    def __str__(self):
        return self.name


class InventorySettings(CompanyOwnedModel):
    business_name = models.CharField(max_length=180, default='My Business')
    currency = models.CharField(max_length=3, default='ZAR')
    default_unit = models.CharField(max_length=30, default='units')
    default_reorder_level = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'))
    low_stock_alerts = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company'], name='inventory_settings_company')]

    @classmethod
    def load(cls):
        from apps.companies.tenancy import owned_company_id
        instance, _ = cls.objects.get_or_create(company_id=owned_company_id())
        return instance

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class StockLocation(CompanyOwnedModel):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=140)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='inventory_stocklocation_code_company')]
        ordering = ['name']

    def __str__(self):
        return self.name


class StockMovement(CompanyOwnedModel):
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


class ReorderRule(CompanyOwnedModel):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reorder_rules')
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name='reorder_rules')
    minimum_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'product', 'location'], name='inventory_unique_reorder_rule')]


class ProductInventoryProfile(CompanyOwnedModel):
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, related_name='inventory_profile')
    category = models.ForeignKey(InventoryCategory, null=True, blank=True, on_delete=models.PROTECT, related_name='product_profiles')
    unit = models.CharField(max_length=30, default='units')
    preferred_supplier = models.ForeignKey('purchasing.Supplier', null=True, blank=True, on_delete=models.SET_NULL, related_name='preferred_for_products')
    stock_reference = models.CharField(max_length=100, blank=True)
    created_through_inventory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product__name']

