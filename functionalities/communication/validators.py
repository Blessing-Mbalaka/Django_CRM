"""
functionalities/communication/validators.py
Business rule validation for communication log operations.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_contact_date_not_future(contact_date):
    """Raise ValidationError if contact date is in the future."""
    if contact_date and contact_date > timezone.now().date():
        raise ValidationError('Contact date cannot be in the future.')


def validate_engagement_is_active(engagement):
    """Warn if logging contact on a closed/lost engagement."""
    if engagement and engagement.status in ('closed', 'lost'):
        raise ValidationError(
            f'Engagement "{engagement.title}" is {engagement.status}. '
            'Log contact against an active engagement instead.'
        )
