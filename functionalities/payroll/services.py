from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.payroll.models import PayRun


@transaction.atomic
def approve_pay_run(*, pay_run, user):
    pay_run = PayRun.objects.select_for_update().prefetch_related('payslips').get(pk=pay_run.pk)
    if pay_run.status != PayRun.Status.DRAFT:
        raise ValidationError('Only draft pay runs can be approved.')
    if not pay_run.payslips.exists():
        raise ValidationError('Add at least one payslip before approval.')
    if any(slip.net_pay < 0 for slip in pay_run.payslips.all()):
        raise ValidationError('Payslip deductions cannot exceed gross pay.')
    pay_run.status = PayRun.Status.APPROVED
    pay_run.approved_by = user
    pay_run.approved_at = timezone.now()
    pay_run.save(update_fields=['status', 'approved_by', 'approved_at'])
    from functionalities.accounting.posting import post_payroll_accrual
    post_payroll_accrual(pay_run)
    return pay_run


@transaction.atomic
def mark_pay_run_paid(*, pay_run, user):
    pay_run = PayRun.objects.select_for_update().get(pk=pay_run.pk)
    if pay_run.status != PayRun.Status.APPROVED:
        raise ValidationError('Only approved pay runs can be marked paid.')
    from functionalities.accounting.posting import post_payroll_payment
    post_payroll_payment(pay_run, user)
    pay_run.status = PayRun.Status.PAID
    pay_run.paid_at = timezone.now()
    pay_run.save(update_fields=['status', 'paid_at'])
    return pay_run
