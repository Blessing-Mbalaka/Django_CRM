from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from functionalities.inventory.services import record_movement, stock_on_hand
from apps.products.models import Product
from apps.purchasing.models import Supplier
from .models import InventoryCategory, InventorySettings, ProductInventoryProfile, ReorderRule, StockLocation, StockMovement


class InventoryCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='product_profiles.count', read_only=True)

    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'description', 'is_active', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'product_count', 'created_at', 'updated_at']


class InventorySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySettings
        fields = ['id', 'business_name', 'currency', 'default_unit', 'default_reorder_level', 'low_stock_alerts', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class InventoryProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=InventoryCategory.objects.filter(is_active=True), allow_null=True, required=False)
    unit = serializers.CharField(max_length=30, required=False)
    preferred_supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.filter(is_active=True), allow_null=True, required=False)
    stock_reference = serializers.CharField(max_length=100, allow_blank=True, required=False)
    opening_quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0, write_only=True, required=False, default=0)
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.filter(is_active=True), write_only=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'description', 'cost_price', 'sales_price', 'tax_rate', 'is_active', 'category', 'unit', 'preferred_supplier', 'stock_reference', 'opening_quantity', 'location', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _profile_data(self, validated_data):
        return {field: validated_data.pop(field) for field in ('category', 'unit', 'preferred_supplier', 'stock_reference') if field in validated_data}

    def validate(self, attrs):
        if attrs.get('opening_quantity', 0) and not attrs.get('location'):
            raise serializers.ValidationError({'location': 'A location is required for opening stock.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        opening = validated_data.pop('opening_quantity', 0)
        location = validated_data.pop('location', None)
        profile_data = self._profile_data(validated_data)
        product = Product.objects.create(product_type=Product.Type.STOCK, **validated_data)
        defaults = {'unit': InventorySettings.load().default_unit, 'created_through_inventory': True, **profile_data}
        ProductInventoryProfile.objects.create(product=product, **defaults)
        if opening:
            record_movement(product=product, location=location, movement_type=StockMovement.Type.RECEIPT, quantity=opening, occurred_on=timezone.localdate(), user=self.context['request'].user, reference='Opening stock')
        return product

    def update(self, instance, validated_data):
        validated_data.pop('opening_quantity', None)
        validated_data.pop('location', None)
        profile_data = self._profile_data(validated_data)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        profile, _ = ProductInventoryProfile.objects.get_or_create(product=instance, defaults={'unit': InventorySettings.load().default_unit})
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = ProductInventoryProfile.objects.filter(product=instance).first()
        data.update({
            'category': profile.category_id if profile else None,
            'category_name': profile.category.name if profile and profile.category else 'Uncategorised',
            'unit': profile.unit if profile else InventorySettings.load().default_unit,
            'preferred_supplier': profile.preferred_supplier_id if profile else None,
            'supplier_name': profile.preferred_supplier.name if profile and profile.preferred_supplier else 'Not assigned',
            'stock_reference': profile.stock_reference if profile else '',
        })
        return data


class StockLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLocation
        fields = ['id', 'code', 'name', 'is_active']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    signed_quantity = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'product_name', 'location', 'location_name', 'movement_type', 'quantity', 'signed_quantity', 'unit_cost', 'reference', 'source_type', 'source_id', 'occurred_on', 'created_by', 'created_at']
        read_only_fields = ['id', 'signed_quantity', 'created_by', 'created_at']

    def create(self, validated_data):
        try:
            return record_movement(user=self.context['request'].user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class ReorderRuleSerializer(serializers.ModelSerializer):
    on_hand = serializers.SerializerMethodField()

    class Meta:
        model = ReorderRule
        fields = ['id', 'product', 'location', 'minimum_quantity', 'reorder_quantity', 'on_hand']

    def get_on_hand(self, obj):
        return stock_on_hand(product=obj.product, location=obj.location)

