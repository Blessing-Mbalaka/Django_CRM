"""
functionalities/finance/services.py
All business logic for financial tracking and revenue analysis.
"""
from django.db.models import Sum, Count, Q

from apps.finance.models import FinancialRecord
from apps.engagements.models import Engagement


def get_finance_overview():
    """
    Return high-level financial KPIs:
      - total confirmed revenue
      - total pipeline value
      - total expenses
      - unpaid revenue count
      - recent records
    """
    agg = FinancialRecord.objects.aggregate(
        revenue=Sum('amount', filter=Q(record_type='revenue')),
        pipeline=Sum('amount', filter=Q(record_type='pipeline')),
        expenses=Sum('amount', filter=Q(record_type='expense')),
        unpaid_count=Count('id', filter=Q(record_type='revenue', is_paid=False)),
    )
    recent_records = (
        FinancialRecord.objects
        .select_related('engagement__client', 'engagement__centre')
        .order_by('-date')[:20]
    )
    return {
        'total_revenue':  agg['revenue']  or 0,
        'total_pipeline': agg['pipeline'] or 0,
        'total_expenses': agg['expenses'] or 0,
        'unpaid_count':   agg['unpaid_count'] or 0,
        'recent_records': recent_records,
    }


def get_centre_revenue_breakdown():
    """
    Return per-centre confirmed revenue totals, ordered by highest revenue.
    Each item: {'centre__name': ..., 'total': ...}
    """
    return (
        FinancialRecord.objects
        .filter(record_type='revenue')
        .values('engagement__centre__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )


def get_top_clients_by_revenue(limit=5):
    """
    Return the top clients by confirmed revenue.
    Each item: {'engagement__client__name': ..., 'total': ...}
    """
    return (
        FinancialRecord.objects
        .filter(record_type='revenue')
        .values('engagement__client__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:limit]
    )


def get_pipeline_by_status():
    """
    Return pipeline value broken down by engagement status.
    Useful for prospect-vs-active pipeline split.
    """
    return (
        FinancialRecord.objects
        .filter(record_type='pipeline')
        .values('engagement__status')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
