"""
functionalities/alerts/services.py
Alert business logic: querying, generation pipeline, and resolution.
"""
from django.utils import timezone

from apps.alerts.models import Alert


# ── Queries ──────────────────────────────────────────────────────────────────

def get_active_alerts(severity=None, alert_type=None):
    """Return all unresolved alerts, optionally filtered."""
    qs = Alert.objects.filter(is_resolved=False).select_related('client', 'engagement')
    if severity:
        qs = qs.filter(severity=severity)
    if alert_type:
        qs = qs.filter(alert_type=alert_type)
    return qs.order_by('-severity', '-created_at')


def get_all_alerts(include_resolved=False):
    qs = Alert.objects.select_related('client', 'engagement')
    if not include_resolved:
        qs = qs.filter(is_resolved=False)
    return qs.order_by('-created_at')


# ── Alert Generators ─────────────────────────────────────────────────────────

def generate_no_contact_alerts(threshold_days=30):
    """
    Scan active/prospect engagements for those with no contact beyond the
    threshold. Creates an alert if one does not already exist.
    Returns the number of new alerts created.
    """
    from apps.engagements.models import Engagement

    cutoff = timezone.now().date()
    created = 0

    engagements = Engagement.objects.filter(
        status__in=('active', 'prospect'),
    ).select_related('client')

    for eng in engagements:
        days = eng.days_since_contact
        if days is None or days < threshold_days:
            continue

        severity = 'critical' if days >= 90 else ('high' if days >= 60 else 'medium')
        already_exists = Alert.objects.filter(
            engagement=eng,
            alert_type='no_contact',
            is_resolved=False,
        ).exists()

        if not already_exists:
            Alert.objects.create(
                title=f'No contact: {eng.title}',
                description=(
                    f'Engagement "{eng.title}" (client: {eng.client.name}) '
                    f'has had no contact for {days} days.'
                ),
                alert_type='no_contact',
                severity=severity,
                engagement=eng,
                client=eng.client,
            )
            created += 1

    return created


def generate_overdue_payment_alerts():
    """
    Scan revenue records that are unpaid and past their date.
    Returns the number of new alerts created.
    """
    from apps.finance.models import FinancialRecord

    today = timezone.now().date()
    created = 0

    overdue = FinancialRecord.objects.filter(
        record_type='revenue',
        is_paid=False,
        date__lt=today,
    ).select_related('engagement__client')

    for record in overdue:
        already_exists = Alert.objects.filter(
            engagement=record.engagement,
            alert_type='payment_due',
            is_resolved=False,
        ).exists()

        if not already_exists:
            Alert.objects.create(
                title=f'Payment overdue: {record.engagement.title}',
                description=(
                    f'R{record.amount} revenue record for '
                    f'"{record.engagement}" is unpaid (due {record.date}).'
                ),
                alert_type='payment_due',
                severity='high',
                engagement=record.engagement,
                client=record.engagement.client,
            )
            created += 1

    return created


def generate_overlap_alerts():
    """
    Detect engagements where the same client has multiple active/prospect
    engagements across different centres (overlap detection rule).
    Returns the number of new alerts created.
    """
    from apps.engagements.models import Engagement
    from django.db.models import Count

    created = 0

    # Find clients with more than 1 active/prospect engagement
    duplicates = (
        Engagement.objects
        .filter(status__in=('active', 'prospect'))
        .values('client')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )

    for item in duplicates:
        engs = Engagement.objects.filter(
            client_id=item['client'],
            status__in=('active', 'prospect'),
        ).select_related('client', 'centre')

        for eng in engs:
            already_exists = Alert.objects.filter(
                engagement=eng,
                alert_type='overlap',
                is_resolved=False,
            ).exists()

            if not already_exists:
                Alert.objects.create(
                    title=f'Engagement overlap: {eng.client.name}',
                    description=(
                        f'Client "{eng.client.name}" has multiple active/prospect '
                        f'engagements. Review for potential overlap.'
                    ),
                    alert_type='overlap',
                    severity='medium',
                    engagement=eng,
                    client=eng.client,
                )
                created += 1

    return created


# ── Pipeline Runner ───────────────────────────────────────────────────────────

def run_alert_pipeline():
    """
    Run all alert generators in sequence.
    Returns a summary dict of new alerts created per type.
    """
    return {
        'no_contact':    generate_no_contact_alerts(threshold_days=30),
        'payment_due':   generate_overdue_payment_alerts(),
        'overlap':       generate_overlap_alerts(),
    }


# ── Resolution ───────────────────────────────────────────────────────────────

def resolve_alert(pk):
    """Mark an alert resolved. Returns the updated Alert."""
    alert = Alert.objects.get(pk=pk)
    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.save(update_fields=['is_resolved', 'resolved_at'])
    return alert
