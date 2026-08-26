from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class PayrollEmployee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='payroll_profile')
    employee_number = models.CharField(max_length=40, unique=True)
    tax_number = models.CharField(max_length=30, blank=True)
    monthly_basic = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee_number']

    def __str__(self):
        return f'{self.employee_number} - {self.user.get_full_name() or self.user.username}'


class PayRun(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'

    period_start = models.DateField()
    period_end = models.DateField()
    payment_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_pay_runs')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_pay_runs')
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end', '-id']
        constraints = [models.UniqueConstraint(fields=['period_start', 'period_end'], name='payroll_unique_pay_run_period')]

    @property
    def gross_total(self):
        return sum((slip.gross_pay for slip in self.payslips.all()), Decimal('0.00'))

    @property
    def deductions_total(self):
        return sum((slip.total_deductions for slip in self.payslips.all()), Decimal('0.00'))

    @property
    def net_total(self):
        return sum((slip.net_pay for slip in self.payslips.all()), Decimal('0.00'))

    def __str__(self):
        return f'{self.period_start:%Y-%m-%d} to {self.period_end:%Y-%m-%d}'


class Payslip(models.Model):
    pay_run = models.ForeignKey(PayRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.PROTECT, related_name='payslips')
    basic_salary = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    overtime = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    allowances = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    paye = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    uif_employee = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    uif_employer = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    other_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee__employee_number']
        constraints = [models.UniqueConstraint(fields=['pay_run', 'employee'], name='payroll_unique_employee_per_run')]

    @property
    def gross_pay(self):
        return self.basic_salary + self.overtime + self.allowances

    @property
    def total_deductions(self):
        return self.paye + self.uif_employee + self.other_deductions

    @property
    def net_pay(self):
        return self.gross_pay - self.total_deductions

    def __str__(self):
        return f'{self.employee} - {self.pay_run}'
