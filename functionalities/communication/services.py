"""
functionalities/communication/services.py
Relationship health, contact tracking, and communication log logic.
"""
from django.utils import timezone
from django.db.models import Count, Max

from apps.communication.models import CommunicationLog
from apps.engagements.models import Engagement


# ── Health Scoring ────────────────────────────────────────────────────────────

def get_health_score(engagement):
    """
    Compute a health score for a single engagement based on days_since_contact.
    Returns a dict: {score, label, colour, days}
    """
    days = engagement.days_since_contact
    if days is None:
        return {'score': 0, 'label': 'No Contact', 'colour': 'danger',  'days': None}
    if days <= 30:
        return {'score': 3, 'label': 'Healthy',    'colour': 'success', 'days': days}
    if days <= 60:
        return {'score': 2, 'label': 'Amber',      'colour': 'warning', 'days': days}
    if days <= 90:
        return {'score': 1, 'label': 'At Risk',    'colour': 'orange',  'days': days}
    return     {'score': 0, 'label': 'Critical',   'colour': 'danger',  'days': days}


# ── Risk Buckets ──────────────────────────────────────────────────────────────

def get_relationship_risk_report():
    """
    Group active/prospect engagements into contact recency buckets.
    Returns dict with keys: healthy, amber, at_risk, critical, no_contact
    """
    engagements = (
        Engagement.objects
        .filter(status__in=('active', 'prospect'))
        .select_related('client', 'centre', 'lead_owner')
    )
    buckets = {'healthy': [], 'amber': [], 'at_risk': [], 'critical': [], 'no_contact': []}
    for eng in engagements:
        days = eng.days_since_contact
        if days is None:
            buckets['no_contact'].append(eng)
        elif days <= 30:
            buckets['healthy'].append(eng)
        elif days <= 60:
            buckets['amber'].append(eng)
        elif days <= 90:
            buckets['at_risk'].append(eng)
        else:
            buckets['critical'].append(eng)
    return buckets


# ── Log Contact ───────────────────────────────────────────────────────────────

def log_contact(engagement, user, contact_type, summary, contact_date=None):
    """
    Create a CommunicationLog entry AND update the engagement's last_contact
    field in one atomic operation.
    Returns the created CommunicationLog instance.
    """
    date = contact_date or timezone.now().date()
    log = CommunicationLog.objects.create(
        engagement=engagement,
        logged_by=user,
        contact_type=contact_type,
        summary=summary,
        contact_date=date,
    )
    # Keep last_contact up to date
    if engagement.last_contact is None or date > engagement.last_contact:
        engagement.last_contact = date
        engagement.save(update_fields=['last_contact', 'updated_at'])
    return log


# ── Overview ──────────────────────────────────────────────────────────────────

def get_comms_health_context():
    """
    Aggregate everything for the communication health template.
    """
    recent_logs = (
        CommunicationLog.objects
        .select_related('engagement__client', 'logged_by')
        .order_by('-contact_date')[:30]
    )
    risk_report = get_relationship_risk_report()
    return {
        'recent_logs':   recent_logs,
        'risk_report':   risk_report,
        'risk_counts': {
            'healthy':    len(risk_report['healthy']),
            'amber':      len(risk_report['amber']),
            'at_risk':    len(risk_report['at_risk']),
            'critical':   len(risk_report['critical']),
            'no_contact': len(risk_report['no_contact']),
        },
    }
