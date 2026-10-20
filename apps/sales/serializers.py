from apps.companies.serializers import CompanyModelSerializer
from rest_framework import serializers

from .models import Fulfilment, SalesOrder, SalesOrderLine


class SalesOrderLineSerializer(CompanyModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    net_amount = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = SalesOrderLine
        fields = ['id', 'sales_order', 'product', 'product_name', 'description', 'quantity', 'fulfilled_quantity', 'unit_price', 'tax_rate', 'net_amount', 'tax_amount']
        read_only_fields = ['id', 'fulfilled_quantity']

    def validate_sales_order(self, sales_order):
        if sales_order.status != SalesOrder.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be changed on draft sales orders.')
        return sales_order


class SalesOrderSerializer(CompanyModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    tax_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = SalesOrder
        fields = ['id', 'number', 'client', 'client_name', 'engagement', 'location', 'invoice', 'status', 'order_date', 'notes', 'created_by', 'created_at', 'updated_at', 'subtotal', 'tax_total', 'total', 'lines']
        read_only_fields = ['id', 'number', 'invoice', 'status', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        if self.instance and self.instance.status != SalesOrder.Status.DRAFT:
            raise serializers.ValidationError('Only draft sales orders can be edited.')
        return attrs


class FulfilmentSerializer(CompanyModelSerializer):
    lines = serializers.SerializerMethodField()

    class Meta:
        model = Fulfilment
        fields = ['id', 'sales_order', 'fulfilled_on', 'reference', 'fulfilled_by', 'created_at', 'lines']
        read_only_fields = fields

    def get_lines(self, obj):
        return [{'sales_order_line': line.sales_order_line_id, 'quantity': line.quantity} for line in obj.lines.all()]
