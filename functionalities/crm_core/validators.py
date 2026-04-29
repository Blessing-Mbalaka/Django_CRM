"""
functionalities/crm_core/validators.py
System-level validation rules.
"""
from django.core.exceptions import ValidationError


def validate_user_has_centre(user):
    """Raise ValidationError if a non-dean user has no centre assigned."""
    if user.role not in ('dean', 'admin') and not getattr(user, 'centre', None):
        raise ValidationError(
            f'User "{user.get_full_name()}" must be assigned to a centre before '
            'taking this action.'
        )
