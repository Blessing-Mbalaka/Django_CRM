from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from functionalities.purchasing.services import approve_purchase_order, receive_purchase_order
from .models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine, Supplier
from .serializers import GoodsReceiptSerializer, PurchaseOrderLineSerializer, PurchaseOrderSerializer, SupplierSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]


class SupplierViewSet(ManagementWriteViewSet):
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()


class PurchaseOrderViewSet(ManagementWriteViewSet):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.select_related('supplier', 'location', 'created_by').prefetch_related('lines__product')

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
            receipt = receive_purchase_order(purchase_order=self.get_object(), received_on=request.data.get('received_on') or timezone.localdate(), reference=request.data.get('reference', ''), user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(GoodsReceiptSerializer(receipt).data)


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
    queryset = GoodsReceipt.objects.select_related('purchase_order', 'received_by')
