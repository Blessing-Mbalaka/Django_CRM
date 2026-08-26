from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_line_amounts(*, debit, credit):
    if debit < 0 or credit < 0:
        raise ValidationError('Debit and credit values cannot be negative.')
    if (debit == Decimal('0.00')) == (credit == Decimal('0.00')):
        raise ValidationError('Each journal line must contain either a debit or a credit.')


def validate_period_is_open(*, entry_date, periods):
    period = periods.filter(start_date__lte=entry_date, end_date__gte=entry_date).first()
    if period and period.is_closed:
        raise ValidationError('The accounting period is closed.')

