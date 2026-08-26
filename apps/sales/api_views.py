from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from apps.billing.serializers import InvoiceSerializer
from functionalities.sales.services import confirm_sales_order, fulfil_sales_order, invoice_sales_order
from .models import Fulfilment, SalesOrder, SalesOrderLine
from .serializers import FulfilmentSerializer, SalesOrderLineSerializer, SalesOrderSerializer


class ManagementWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]


class SalesOrderViewSet(ManagementWriteViewSet):
    serializer_class = SalesOrderSerializer
    queryset = SalesOrder.objects.select_related('client', 'engagement', 'location', 'invoice', 'created_by').prefetch_related('lines__product')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != SalesOrder.Status.DRAFT:
            raise serializers.ValidationError('Only draft sales orders can be deleted.')
        instance.delete()

    def _service(self, callback, **kwargs):
        try:
            return callback(sales_order=self.get_object(), **kwargs)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        return Response(self.get_serializer(self._service(confirm_sales_order)).data)

    @action(detail=True, methods=['post'])
    def fulfil(self, request, pk=None):
        fulfilment = self._service(fulfil_sales_order, fulfilled_on=request.data.get('fulfilled_on') or timezone.localdate(), reference=request.data.get('reference', ''), user=request.user)
        return Response(FulfilmentSerializer(fulfilment).data)

    @action(detail=True, methods=['post'])
    def invoice(self, request, pk=None):
        if not request.data.get('due_date'):
            raise serializers.ValidationError({'due_date': 'Due date is required.'})
        invoice = self._service(invoice_sales_order, due_date=request.data['due_date'], user=request.user)
        return Response(InvoiceSerializer(invoice, context={'request': request}).data)


class SalesOrderLineViewSet(ManagementWriteViewSet):
    serializer_class = SalesOrderLineSerializer
    queryset = SalesOrderLine.objects.select_related('sales_order', 'product')

    def perform_destroy(self, instance):
        if instance.sales_order.status != SalesOrder.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be deleted from draft sales orders.')
        instance.delete()


class FulfilmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FulfilmentSerializer
    queryset = Fulfilment.objects.select_related('sales_order', 'fulfilled_by')
