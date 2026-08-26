from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from functionalities.billing.services import record_payment
from .models import Invoice, InvoiceLine, Payment


class InvoiceLineSerializer(serializers.ModelSerializer):
    net_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ['id', 'invoice', 'description', 'quantity', 'unit_price', 'tax_rate', 'position', 'net_amount', 'tax_amount']
        read_only_fields = ['id']

    def validate_invoice(self, invoice):
        if invoice.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be changed on draft invoices.')
        return invoice

    def validate(self, attrs):
        invoice = attrs.get('invoice', getattr(self.instance, 'invoice', None))
        if invoice and invoice.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be changed on draft invoices.')
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tax_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'number', 'client', 'client_name', 'engagement', 'status', 'issue_date', 'due_date', 'currency', 'notes', 'created_by', 'lines', 'subtotal', 'tax_total', 'total', 'amount_paid', 'balance_due', 'created_at', 'updated_at']
        read_only_fields = ['id', 'number', 'status', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        issue_date = attrs.get('issue_date', getattr(self.instance, 'issue_date', None))
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError({'due_date': 'Due date cannot be before the issue date.'})
        if self.instance and self.instance.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Only draft invoices can be edited.')
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'paid_on', 'reference', 'recorded_by', 'created_at']
        read_only_fields = ['id', 'recorded_by', 'created_at']

    def create(self, validated_data):
        try:
            return record_payment(user=self.context['request'].user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
