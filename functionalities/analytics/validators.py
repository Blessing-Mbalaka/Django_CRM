"""
functionalities/analytics/validators.py
Validation for analytics / reporting operations.
"""
from django.core.exceptions import ValidationError


def validate_date_range(start_date, end_date):
    """Raise ValidationError if end_date precedes start_date for report filters."""
    if start_date and end_date and end_date < start_date:
        raise ValidationError('Report end date cannot be before start date.')
