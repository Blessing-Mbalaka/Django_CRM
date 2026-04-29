"""
functionalities/analytics/services.py
Reporting, KPI aggregation, and institutional intelligence.
"""
from django.db.models import Count, Sum, Avg, Q

from apps.engagements.models import Engagement
from apps.finance.models import FinancialRecord
from apps.clients.models import Client
from apps.centres.models import Centre
from apps.alerts.models import Alert
from apps.communication.models import CommunicationLog


def get_pipeline_analysis():
    """
    Prospect vs Active engagement counts and pipeline values.
    """
    statuses = ('prospect', 'active', 'on_hold', 'closed', 'lost')
    counts = (
        Engagement.objects
        .filter(status__in=statuses)
        .values('status')
        .annotate(count=Count('id'))
    )
    count_map = {row['status']: row['count'] for row in counts}

    pipeline = (
        FinancialRecord.objects
        .filter(record_type='pipeline')
        .values('engagement__status')
        .annotate(total=Sum('amount'))
    )
    pipeline_map = {row['engagement__status']: row['total'] for row in pipeline}

    return {
        'counts':   {s: count_map.get(s, 0) for s in statuses},
        'pipeline': {s: pipeline_map.get(s, 0) for s in statuses},
    }


def get_centre_performance():
    """
    Per-centre summary: engagement count, active count, revenue, staff count.
    Returns a list of dicts sorted by revenue descending.
    """
    centres = Centre.objects.filter(is_active=True).prefetch_related(
        'engagements', 'users', 'staff_members'
    )

    revenue_map = {
        row['engagement__centre_id']: row['total']
        for row in FinancialRecord.objects
        .filter(record_type='revenue')
        .values('engagement__centre_id')
        .annotate(total=Sum('amount'))
    }

    rows = []
    for c in centres:
        eng_qs = c.engagements.all()
        rows.append({
            'centre':           c,
            'total_engagements': eng_qs.count(),
            'active_engagements': eng_qs.filter(status='active').count(),
            'revenue':          revenue_map.get(c.pk, 0) or 0,
            'staff_count':      c.staff_members.filter(is_active=True).count(),
        })

    rows.sort(key=lambda r: r['revenue'], reverse=True)
    return rows


def get_engagement_health_scores():
    """
    Return engagements with a computed health score:
      - Green  (score=3): last contact ≤ 30 days
      - Amber  (score=2): last contact 31-60 days
      - Orange (score=1): last contact 61-90 days
      - Red    (score=0): last contact > 90 days or never
    """
    engagements = (
        Engagement.objects
        .filter(status__in=('active', 'prospect'))
        .select_related('client', 'centre', 'lead_owner')
    )
    result = []
    for eng in engagements:
        days = eng.days_since_contact
        if days is None:
            score, label, colour = 0, 'No Contact', 'danger'
        elif days <= 30:
            score, label, colour = 3, 'Healthy',    'success'
        elif days <= 60:
            score, label, colour = 2, 'Amber',      'warning'
        elif days <= 90:
            score, label, colour = 1, 'At Risk',    'orange'
        else:
            score, label, colour = 0, 'Critical',   'danger'
        result.append({
            'engagement': eng,
            'days':       days,
            'score':      score,
            'label':      label,
            'colour':     colour,
        })
    result.sort(key=lambda r: r['score'])
    return result


def get_staff_activity(limit=10):
    """
    Return staff ranked by number of communication log entries (descending).
    """
    return (
        CommunicationLog.objects
        .values('logged_by__id', 'logged_by__first_name', 'logged_by__last_name')
        .annotate(log_count=Count('id'))
        .order_by('-log_count')[:limit]
    )


def get_client_engagement_intensity(limit=10):
    """
    Return clients ranked by number of engagements (all statuses).
    """
    return (
        Client.objects
        .annotate(engagement_count=Count('engagements'))
        .order_by('-engagement_count')[:limit]
    )


def get_reports_context():
    """
    Aggregate all analytics for the reports template.
    This is the single call a view makes — no logic in views.
    """
    return {
        'pipeline_analysis':      get_pipeline_analysis(),
        'centre_performance':     get_centre_performance(),
        'health_scores':          get_engagement_health_scores(),
        'staff_activity':         get_staff_activity(),
        'top_clients':            get_client_engagement_intensity(),
        'total_clients':          Client.objects.count(),
        'total_engagements':      Engagement.objects.count(),
        'unresolved_alerts':      Alert.objects.filter(is_resolved=False).count(),
        'total_revenue':          FinancialRecord.objects.filter(
                                      record_type='revenue'
                                  ).aggregate(t=Sum('amount'))['t'] or 0,
        'total_pipeline':         FinancialRecord.objects.filter(
                                      record_type='pipeline'
                                  ).aggregate(t=Sum('amount'))['t'] or 0,
    }
