"""
functionalities/alerts/validators.py
Business rule validation for alert operations.
"""
from django.core.exceptions import ValidationError


def validate_alert_has_context(engagement, client):
    """At least one of engagement or client must be provided for context."""
    if not engagement and not client:
        raise ValidationError(
            'An alert must be linked to either an engagement or a client.'
        )
