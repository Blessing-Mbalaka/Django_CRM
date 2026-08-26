from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import IsDeanDirectorOrAdmin
from functionalities.billing.services import issue_invoice
from .models import Invoice, InvoiceLine, Payment
from .serializers import InvoiceLineSerializer, InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.select_related('client', 'engagement', 'created_by').prefetch_related('lines', 'payments')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Only draft invoices can be deleted.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        try:
            invoice = issue_invoice(invoice=self.get_object())
        except ValueError as exc:
            raise serializers.ValidationError({'invoice': str(exc)})
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)


class InvoiceLineViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceLineSerializer
    queryset = InvoiceLine.objects.select_related('invoice')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(invoice_id=self.request.query_params['invoice']) if self.request.query_params.get('invoice') else qs

    def perform_destroy(self, instance):
        if instance.invoice.status != Invoice.Status.DRAFT:
            raise serializers.ValidationError('Lines can only be deleted from draft invoices.')
        instance.delete()


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    queryset = Payment.objects.select_related('invoice', 'recorded_by')

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ('list', 'retrieve') else [IsDeanDirectorOrAdmin()]
