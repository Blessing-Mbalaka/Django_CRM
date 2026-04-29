"""
functionalities/people/validators.py
Validation for people / staff directory operations.
"""
from django.core.exceptions import ValidationError


def validate_unique_email(email, exclude_pk=None):
    """Raise ValidationError if another user has this email."""
    from apps.accounts.models import User
    qs = User.objects.filter(email__iexact=email)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(f'A user with email "{email}" already exists.')


def validate_role_centre_pairing(role, centre):
    """Dean and admin roles do not require a centre assignment."""
    if role not in ('dean', 'admin') and not centre:
        raise ValidationError(
            f'Role "{role}" must be assigned to a centre.'
        )
