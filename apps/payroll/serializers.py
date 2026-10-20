from apps.companies.serializers import CompanyModelSerializer
from django.db import transaction
from rest_framework import serializers

from .models import PayrollEmployee, PayRun, Payslip


class PayrollEmployeeSerializer(CompanyModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='user.centre.name', read_only=True)

    class Meta:
        model = PayrollEmployee
        fields = ['id', 'user', 'employee_name', 'department_name', 'employee_number', 'tax_number', 'monthly_basic', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_employee_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class PayslipSerializer(CompanyModelSerializer):
    employee_name = serializers.SerializerMethodField()
    gross_pay = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    net_pay = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Payslip
        fields = ['id', 'pay_run', 'employee', 'employee_name', 'basic_salary', 'overtime', 'allowances', 'paye', 'uif_employee', 'uif_employer', 'other_deductions', 'gross_pay', 'total_deductions', 'net_pay', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name() or obj.employee.user.username

    def validate(self, attrs):
        pay_run = attrs.get('pay_run', getattr(self.instance, 'pay_run', None))
        employee = attrs.get('employee', getattr(self.instance, 'employee', None))
        if pay_run and pay_run.status != PayRun.Status.DRAFT:
            raise serializers.ValidationError('Payslips can only be changed while the pay run is draft.')
        if employee and not employee.is_active:
            raise serializers.ValidationError({'employee': 'Select an active payroll employee.'})
        values = {name: attrs.get(name, getattr(self.instance, name, 0)) for name in ['basic_salary', 'overtime', 'allowances', 'paye', 'uif_employee', 'other_deductions']}
        gross = values['basic_salary'] + values['overtime'] + values['allowances']
        deductions = values['paye'] + values['uif_employee'] + values['other_deductions']
        if deductions > gross:
            raise serializers.ValidationError('Employee deductions cannot exceed gross pay.')
        return attrs


class InitialPayslipSerializer(serializers.Serializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=PayrollEmployee.objects.filter(is_active=True))
    basic_salary = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    overtime = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    allowances = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    paye = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    uif_employee = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    uif_employer = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    other_deductions = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)

    def validate(self, attrs):
        gross = attrs['basic_salary'] + attrs['overtime'] + attrs['allowances']
        deductions = attrs['paye'] + attrs['uif_employee'] + attrs['other_deductions']
        if deductions > gross:
            raise serializers.ValidationError('Employee deductions cannot exceed gross pay.')
        return attrs


class PayRunSerializer(CompanyModelSerializer):
    payslips = PayslipSerializer(many=True, read_only=True)
    gross_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    deductions_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    net_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    initial_payslip = InitialPayslipSerializer(write_only=True, required=False)

    class Meta:
        model = PayRun
        fields = ['id', 'period_start', 'period_end', 'payment_date', 'status', 'created_by', 'approved_by', 'approved_at', 'paid_at', 'created_at', 'gross_total', 'deductions_total', 'net_total', 'initial_payslip', 'payslips']
        read_only_fields = ['id', 'status', 'created_by', 'approved_by', 'approved_at', 'paid_at', 'created_at']

    def validate(self, attrs):
        start, end = attrs.get('period_start'), attrs.get('period_end')
        if start and end and end < start:
            raise serializers.ValidationError({'period_end': 'Period end cannot precede period start.'})
        if start and end and PayRun.objects.filter(period_start=start, period_end=end).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('A pay run already exists for this period.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        initial_payslip = validated_data.pop('initial_payslip', None)
        pay_run = PayRun.objects.create(**validated_data)
        if initial_payslip:
            Payslip.objects.create(pay_run=pay_run, **initial_payslip)
        return pay_run
