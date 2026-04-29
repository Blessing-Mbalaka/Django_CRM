"""
functionalities/finance/validators.py
Business rule validation for financial record operations.
"""
from django.core.exceptions import ValidationError


def validate_positive_amount(amount):
    """Raise ValidationError if amount is not positive."""
    if amount is not None and amount <= 0:
        raise ValidationError('Amount must be greater than zero.')


def validate_record_type_consistency(record_type, is_paid):
    """Pipeline records should not be marked as paid."""
    if record_type == 'pipeline' and is_paid:
        raise ValidationError(
            'Pipeline (forecast) records cannot be marked as paid. '
            'Change the type to Revenue first.'
        )
