"""
functionalities/clients/validators.py
Business rule validation for client operations.
"""
from django.core.exceptions import ValidationError


def validate_client_name_unique(name, exclude_pk=None):
    """Raise ValidationError if another client with this name already exists."""
    from apps.clients.models import Client
    qs = Client.objects.filter(name__iexact=name)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(f'A client named "{name}" already exists.')


def validate_visibility_permission(user, visibility):
    """Only deans/admins may create institutional-visibility clients."""
    if visibility == 'institutional' and not (user.is_ceo or user.role == 'admin'):
        raise ValidationError(
            'Only CEO or Admin users may set visibility to Institutional.'
        )
