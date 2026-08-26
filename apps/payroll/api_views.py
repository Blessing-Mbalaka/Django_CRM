from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.permissions import IsCEOOrAdmin
from functionalities.payroll.services import approve_pay_run, mark_pay_run_paid
from .models import PayrollEmployee, PayRun, Payslip
from .serializers import PayrollEmployeeSerializer, PayRunSerializer, PayslipSerializer


class PayrollEmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCEOOrAdmin]
    serializer_class = PayrollEmployeeSerializer
    queryset = PayrollEmployee.objects.select_related('user__centre').order_by('employee_number')


class PayRunViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCEOOrAdmin]
    serializer_class = PayRunSerializer
    queryset = PayRun.objects.select_related('created_by', 'approved_by').prefetch_related('payslips__employee__user')
    http_method_names = ['get', 'post', 'head', 'options']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        try:
            pay_run = approve_pay_run(pay_run=self.get_object(), user=request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(pay_run).data)

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        try:
            pay_run = mark_pay_run_paid(pay_run=self.get_object())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return Response(self.get_serializer(pay_run).data)


class PayslipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCEOOrAdmin]
    serializer_class = PayslipSerializer
    queryset = Payslip.objects.select_related('pay_run', 'employee__user')

    def perform_destroy(self, instance):
        if instance.pay_run.status != PayRun.Status.DRAFT:
            raise serializers.ValidationError('Payslips can only be deleted while the pay run is draft.')
        instance.delete()
