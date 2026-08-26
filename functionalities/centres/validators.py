"""
functionalities/centres/validators.py
Business rule validation for centre operations.
"""
from django.core.exceptions import ValidationError


def validate_centre_code_unique(code, exclude_pk=None):
    """Raise ValidationError if another centre uses this code."""
    from apps.centres.models import Centre
    qs = Centre.objects.filter(code__iexact=code)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(f'Department code "{code}" is already in use.')
