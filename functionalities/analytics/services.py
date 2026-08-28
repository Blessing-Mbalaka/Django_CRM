"""
functionalities/analytics/services.py
Reporting, KPI aggregation, and institutional intelligence.
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Avg, Q

from apps.engagements.models import Engagement
from apps.finance.models import FinancialRecord
from apps.clients.models import Client
from apps.centres.models import Centre
from apps.alerts.models import Alert
from apps.communication.models import CommunicationLog
from functionalities.finance.services import ledger_actuals, revenue_by_engagement


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

    revenue_map = {}
    for engagement, _client, amount in revenue_by_engagement():
        if engagement and engagement.centre_id:
            revenue_map[engagement.centre_id] = revenue_map.get(engagement.centre_id, 0) + amount

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
        'total_revenue':          ledger_actuals()['revenue'],
        'total_pipeline':         FinancialRecord.objects.filter(
                                      record_type='pipeline'
                                  ).aggregate(t=Sum('amount'))['t'] or 0,
    }


def _parse_activity_date(value, fallback, field):
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: 'Use a valid date in YYYY-MM-DD format.'}) from exc


def _bucket(value, granularity):
    if granularity == 'month':
        return value.replace(day=1)
    if granularity == 'week':
        return value - timedelta(days=value.weekday())
    return value


def _bucket_sequence(start, end, granularity):
    current = _bucket(start, granularity)
    result = []
    while current <= end:
        result.append(current)
        if granularity == 'month':
            current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        elif granularity == 'week':
            current += timedelta(days=7)
        else:
            current += timedelta(days=1)
    return result


def get_business_activity(*, start_date=None, end_date=None, granularity='month', source='all', product=None, location=None, supplier=None):
    """Combine ledger actuals and operational quantities into aligned Plotly series."""
    from django.utils import timezone
    from apps.accounting.models import Account, JournalEntry, JournalLine
    from apps.inventory.models import StockMovement
    from apps.purchasing.models import GoodsReceiptLine, SupplierBill

    today = timezone.localdate()
    end = _parse_activity_date(end_date, today, 'end_date')
    start = _parse_activity_date(start_date, end - timedelta(days=365), 'start_date')
    if start > end:
        raise ValidationError({'end_date': 'End date cannot precede start date.'})
    if granularity not in ('day', 'week', 'month'):
        raise ValidationError({'granularity': 'Choose day, week, or month.'})
    allowed_sources = ('all', 'sales', 'purchasing', 'expenses', 'payroll', 'inventory')
    if source not in allowed_sources:
        raise ValidationError({'source': 'Choose a valid activity source.'})

    buckets = _bucket_sequence(start, end, granularity)
    values = {name: defaultdict(lambda: Decimal('0.00')) for name in ('revenue', 'expenses', 'cash_in', 'cash_out', 'purchasing')}
    quantities = {name: defaultdict(lambda: Decimal('0.000')) for name in ('inventory_level', 'purchase_receipts')}
    inventory_values = defaultdict(lambda: Decimal('0.00'))

    source_types = {
        'sales': ('invoice', 'customer_payment', 'fulfilment'),
        'purchasing': ('supplier_bill', 'supplier_payment'),
        'expenses': ('expense', 'expense_payment'),
        'payroll': ('payroll_accrual', 'payroll_payment'),
        'inventory': ('fulfilment',),
    }
    lines = JournalLine.objects.filter(entry__status__in=(JournalEntry.Status.POSTED, JournalEntry.Status.REVERSED), entry__date__range=(start, end)).select_related('entry', 'account')
    if source != 'all':
        lines = lines.filter(entry__source_type__in=source_types[source])
    for line in lines:
        key = _bucket(line.entry.date, granularity)
        if line.account.account_type == Account.Type.REVENUE:
            values['revenue'][key] += line.credit - line.debit
        elif line.account.account_type == Account.Type.EXPENSE:
            values['expenses'][key] += line.debit - line.credit
        if line.account.system_role == Account.SystemRole.BANK:
            values['cash_in'][key] += line.debit
            values['cash_out'][key] += line.credit

    bills = SupplierBill.objects.exclude(status=SupplierBill.Status.DRAFT).filter(bill_date__range=(start, end)).select_related('purchase_order')
    if supplier:
        bills = bills.filter(purchase_order__supplier_id=supplier)
    if location:
        bills = bills.filter(purchase_order__location_id=location)
    if product:
        bills = bills.filter(purchase_order__lines__product_id=product).distinct()
    if source in ('all', 'purchasing'):
        for bill in bills:
            values['purchasing'][_bucket(bill.bill_date, granularity)] += bill.total

    movements = StockMovement.objects.filter(occurred_on__lte=end).select_related('product', 'location')
    if product:
        movements = movements.filter(product_id=product)
    if location:
        movements = movements.filter(location_id=location)
    opening_quantity = Decimal('0.000')
    opening_value = Decimal('0.00')
    movement_deltas = defaultdict(lambda: Decimal('0.000'))
    value_deltas = defaultdict(lambda: Decimal('0.00'))
    for movement in movements:
        signed_quantity = movement.signed_quantity
        signed_value = signed_quantity * movement.unit_cost
        if movement.occurred_on < start:
            opening_quantity += signed_quantity
            opening_value += signed_value
        else:
            key = _bucket(movement.occurred_on, granularity)
            movement_deltas[key] += signed_quantity
            value_deltas[key] += signed_value

    receipts = GoodsReceiptLine.objects.filter(receipt__received_on__range=(start, end)).select_related('receipt__purchase_order', 'purchase_order_line')
    if supplier:
        receipts = receipts.filter(receipt__purchase_order__supplier_id=supplier)
    if location:
        receipts = receipts.filter(receipt__purchase_order__location_id=location)
    if product:
        receipts = receipts.filter(purchase_order_line__product_id=product)
    for receipt_line in receipts:
        quantities['purchase_receipts'][_bucket(receipt_line.receipt.received_on, granularity)] += receipt_line.quantity

    running_quantity, running_value = opening_quantity, opening_value
    for key in buckets:
        running_quantity += movement_deltas[key]
        running_value += value_deltas[key]
        quantities['inventory_level'][key] = running_quantity
        inventory_values[key] = running_value

    labels = [bucket.isoformat() for bucket in buckets]
    currency = {name: [float(values[name][bucket]) for bucket in buckets] for name in values}
    currency['inventory_value'] = [float(inventory_values[bucket]) for bucket in buckets]
    quantity = {name: [float(quantities[name][bucket]) for bucket in buckets] for name in quantities}
    return {
        'filters': {'start_date': start.isoformat(), 'end_date': end.isoformat(), 'granularity': granularity, 'source': source, 'product': product, 'location': location, 'supplier': supplier},
        'labels': labels,
        'currency': currency,
        'quantity': quantity,
        'summary': {
            'revenue': float(sum(values['revenue'].values(), Decimal('0.00'))),
            'expenses': float(sum(values['expenses'].values(), Decimal('0.00'))),
            'net_profit': float(sum(values['revenue'].values(), Decimal('0.00')) - sum(values['expenses'].values(), Decimal('0.00'))),
            'inventory_level': float(running_quantity),
            'inventory_value': float(running_value),
            'purchasing': float(sum(values['purchasing'].values(), Decimal('0.00'))),
        },
    }
