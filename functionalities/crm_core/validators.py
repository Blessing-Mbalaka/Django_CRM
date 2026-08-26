"""
functionalities/crm_core/validators.py
System-level validation rules.
"""
from django.core.exceptions import ValidationError


def validate_user_has_centre(user):
    """Raise ValidationError if a non-CEO user has no department assigned."""
    if user.role not in ('dean', 'admin') and not getattr(user, 'centre', None):
        raise ValidationError(
            f'User "{user.get_full_name()}" must be assigned to a department before '
            'taking this action.'
        )
