"""
functionalities/engagements/validators.py
Business rule validation for engagement operations.
"""
from django.core.exceptions import ValidationError


def validate_engagement_dates(start_date, end_date):
    """Raise ValidationError if end_date precedes start_date."""
    if start_date and end_date and end_date < start_date:
        raise ValidationError('End date cannot be before the start date.')


def validate_no_duplicate_engagement(client_id, centre_id, exclude_pk=None):
    """
    Raise ValidationError if an active/prospect engagement already exists
    for this client + department combination.
    """
    from apps.engagements.models import Engagement
    qs = Engagement.objects.filter(
        client_id=client_id,
        centre_id=centre_id,
        status__in=('active', 'prospect'),
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(
            'An active or prospect engagement already exists for this client '
            'and department combination. Review for overlap.'
        )
