from rest_framework import serializers

from .models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, Supplier, SupplierBill, SupplierPayment


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'email', 'phone', 'tax_number', 'is_active']


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ['id', 'purchase_order', 'product', 'product_name', 'description', 'quantity', 'unit_cost', 'tax_rate', 'received_quantity', 'line_total']
        read_only_fields = ['id', 'received_quantity']

    def validate_purchase_order(self, purchase_order):
        if purchase_order.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be changed on draft purchase orders.')
        return purchase_order


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    supplier_bill = serializers.IntegerField(source='supplier_bill.id', read_only=True)
    supplier_bill_status = serializers.CharField(source='supplier_bill.status', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'number', 'supplier', 'supplier_name', 'location', 'location_name', 'status', 'order_date', 'expected_date', 'notes', 'created_by', 'created_at', 'updated_at', 'total', 'supplier_bill', 'supplier_bill_status', 'lines']
        read_only_fields = ['id', 'number', 'status', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        if self.instance and self.instance.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError('Only draft purchase orders can be edited.')
        return attrs


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = serializers.SerializerMethodField()

    class Meta:
        model = GoodsReceipt
        fields = ['id', 'purchase_order', 'received_on', 'reference', 'received_by', 'created_at', 'lines']
        read_only_fields = fields

    def get_lines(self, obj):
        return [{'purchase_order_line': line.purchase_order_line_id, 'quantity': line.quantity} for line in obj.lines.all()]


class SupplierBillSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='purchase_order.supplier.name', read_only=True)

    class Meta:
        model = SupplierBill
        fields = ['id', 'purchase_order', 'supplier_name', 'supplier_invoice_number', 'bill_date', 'due_date', 'subtotal', 'tax_total', 'total', 'amount_paid', 'balance_due', 'status', 'journal_entry', 'created_by', 'created_at']
        read_only_fields = fields


class SupplierPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPayment
        fields = ['id', 'supplier_bill', 'amount', 'paid_on', 'reference', 'recorded_by', 'created_at']
        read_only_fields = fields
