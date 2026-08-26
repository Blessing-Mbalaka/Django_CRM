from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from functionalities.purchasing.services import approve_purchase_order, create_supplier_bill, post_supplier_bill, receive_purchase_order
from .models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine, Supplier, SupplierBill
from .serializers import GoodsReceiptSerializer, PurchaseOrderLineSerializer, PurchaseOrderSerializer, SupplierBillSerializer, SupplierSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]


class SupplierViewSet(ManagementWriteViewSet):
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()


class PurchaseOrderViewSet(ManagementWriteViewSet):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.select_related('supplier', 'location', 'created_by', 'supplier_bill').prefetch_related('lines__product')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError('Only draft purchase orders can be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        try:
            order = approve_purchase_order(purchase_order=self.get_object())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        try:
            line_quantities = None
            if 'lines' in request.data:
                try:
                    line_quantities = {line['line']: line['quantity'] for line in request.data['lines']}
                except (KeyError, TypeError):
                    raise serializers.ValidationError({'lines': 'Each line requires line and quantity values.'})
            receipt = receive_purchase_order(purchase_order=self.get_object(), received_on=request.data.get('received_on') or timezone.localdate(), reference=request.data.get('reference', ''), line_quantities=line_quantities, user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(GoodsReceiptSerializer(receipt).data)

    @action(detail=True, methods=['post'], url_path='create-bill')
    def create_bill(self, request, pk=None):
        required = ('supplier_invoice_number', 'due_date')
        missing = [field for field in required if not request.data.get(field)]
        if missing:
            raise serializers.ValidationError({field: 'This field is required.' for field in missing})
        try:
            bill = create_supplier_bill(purchase_order=self.get_object(), supplier_invoice_number=request.data['supplier_invoice_number'], bill_date=request.data.get('bill_date') or timezone.localdate(), due_date=request.data['due_date'], user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(SupplierBillSerializer(bill).data)


class PurchaseOrderLineViewSet(ManagementWriteViewSet):
    serializer_class = PurchaseOrderLineSerializer
    queryset = PurchaseOrderLine.objects.select_related('purchase_order', 'product')

    def perform_destroy(self, instance):
        if instance.purchase_order.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be deleted from draft purchase orders.')
        instance.delete()


class GoodsReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GoodsReceiptSerializer
    queryset = GoodsReceipt.objects.select_related('purchase_order', 'received_by').prefetch_related('lines')


class SupplierBillViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierBillSerializer
    queryset = SupplierBill.objects.select_related('purchase_order__supplier', 'journal_entry', 'created_by')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        try:
            bill = post_supplier_bill(supplier_bill=self.get_object())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(bill).data)
