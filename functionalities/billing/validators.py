from django.core.exceptions import ValidationError


def validate_invoice_dates(*, issue_date, due_date):
    if due_date < issue_date:
        raise ValidationError({'due_date': 'Due date cannot be before the issue date.'})


def validate_payment(*, invoice, amount):
    if invoice.status in (invoice.Status.DRAFT, invoice.Status.VOID):
        raise ValidationError('Payments can only be recorded against an issued invoice.')
    if amount > invoice.balance_due:
        raise ValidationError('Payment cannot exceed the invoice balance.')

