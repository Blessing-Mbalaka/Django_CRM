from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from functionalities.inventory.services import record_movement, stock_on_hand
from .models import ReorderRule, StockLocation, StockMovement


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

