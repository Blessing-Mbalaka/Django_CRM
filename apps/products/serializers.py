from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers

from .models import Product


class ProductSerializer(CompanyModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'product_type', 'description', 'sales_price', 'cost_price', 'tax_rate', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

