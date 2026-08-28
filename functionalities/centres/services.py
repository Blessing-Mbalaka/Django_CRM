"""
functionalities/centres/services.py
Business logic for centre profiles, KPIs, and performance summaries.
"""
from django.db.models import Count, Sum, Q

from apps.centres.models import Centre
from apps.finance.models import FinancialRecord
from apps.alerts.models import Alert
from functionalities.finance.services import revenue_by_engagement


def get_centre_kpis(centre):
    """
    Return a KPI dict for a single Centre instance:
      - total_engagements, active_engagements, prospect_engagements
      - confirmed_revenue, pipeline_value
      - staff_count, unresolved_alerts
    """
    engs = centre.engagements.all()

    revenue = sum((amount for engagement, _client, amount in revenue_by_engagement() if engagement and engagement.centre_id == centre.id), 0)

    pipeline = FinancialRecord.objects.filter(
        engagement__centre=centre, record_type='pipeline'
    ).aggregate(t=Sum('amount'))['t'] or 0

    alerts = Alert.objects.filter(
        engagement__centre=centre, is_resolved=False
    ).count()

    return {
        'total_engagements':   engs.count(),
        'active_engagements':  engs.filter(status='active').count(),
        'prospect_engagements': engs.filter(status='prospect').count(),
        'confirmed_revenue':   revenue,
        'pipeline_value':      pipeline,
        'staff_count':         centre.staff_members.filter(is_active=True).count(),
        'unresolved_alerts':   alerts,
    }


def get_all_centres_summary():
    """
    Return a list of centres, each with KPIs attached as a dict:
      {'centre': Centre, **kpis}
    Ordered by centre name.
    """
    centres = (
        Centre.objects
        .filter(is_active=True)
        .select_related('director')
        .prefetch_related('engagements', 'staff_members')
        .order_by('name')
    )
    return [{'centre': c, **get_centre_kpis(c)} for c in centres]


def get_centre_list(include_inactive=False):
    """Simple queryset for the centre list view."""
    qs = Centre.objects.select_related('director')
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs.order_by('name')


def get_centre_detail_context(pk):
    """
    Full context dict for the centre detail template.
    Raises Centre.DoesNotExist if not found.
    """
    centre = (
        Centre.objects
        .select_related('director')
        .prefetch_related('users', 'staff_members__user', 'engagements__client')
        .get(pk=pk)
    )
    kpis = get_centre_kpis(centre)
    recent_engagements = centre.engagements.select_related('client', 'lead_owner').order_by('-updated_at')[:5]
    staff = centre.staff_members.filter(is_active=True).select_related('user')

    return {
        'centre':             centre,
        'kpis':               kpis,
        'recent_engagements': recent_engagements,
        'staff':              staff,
    }
