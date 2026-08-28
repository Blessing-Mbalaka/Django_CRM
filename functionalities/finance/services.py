"""Ledger-backed actual financial reporting plus pipeline forecasting."""
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum

from apps.accounting.models import Account, JournalEntry, JournalLine
from apps.billing.models import Invoice
from apps.finance.models import FinancialRecord


REPORTABLE = (JournalEntry.Status.POSTED, JournalEntry.Status.REVERSED)
ZERO = Decimal('0.00')


def ledger_actuals():
    totals = defaultdict(lambda: ZERO)
    rows = (JournalLine.objects
            .filter(entry__status__in=REPORTABLE, account__account_type__in=(Account.Type.REVENUE, Account.Type.EXPENSE))
            .values('account__account_type').annotate(debits=Sum('debit'), credits=Sum('credit')))
    for row in rows:
        if row['account__account_type'] == Account.Type.REVENUE:
            totals['revenue'] += row['credits'] - row['debits']
        else:
            totals['expenses'] += row['debits'] - row['credits']
    totals['net_profit'] = totals['revenue'] - totals['expenses']
    return totals


def revenue_by_engagement():
    """Return recognized invoice revenue grouped by engagement without duplicating it."""
    rows = (JournalLine.objects
            .filter(entry__status=JournalEntry.Status.POSTED, entry__source_type='invoice', account__account_type=Account.Type.REVENUE)
            .values('entry__source_id').annotate(credits=Sum('credit'), debits=Sum('debit')))
    amounts = {row['entry__source_id']: row['credits'] - row['debits'] for row in rows}
    invoices = Invoice.objects.filter(id__in=amounts).select_related('engagement__centre', 'client')
    return [(invoice.engagement, invoice.client, amounts[invoice.id]) for invoice in invoices]


def get_finance_overview():
    actuals = ledger_actuals()
    pipeline = FinancialRecord.objects.filter(record_type=FinancialRecord.RecordType.PIPELINE).aggregate(total=Sum('amount'))['total'] or ZERO
    return {
        'total_revenue': actuals['revenue'],
        'total_pipeline': pipeline,
        'total_expenses': actuals['expenses'],
        'net_profit': actuals['net_profit'],
        'unpaid_count': Invoice.objects.filter(status__in=(Invoice.Status.ISSUED, Invoice.Status.PART_PAID)).count(),
        'recent_entries': JournalEntry.objects.filter(status__in=REPORTABLE).prefetch_related('lines').order_by('-date', '-id')[:20],
    }


def get_centre_revenue_breakdown():
    grouped = defaultdict(lambda: ZERO)
    for engagement, _client, amount in revenue_by_engagement():
        grouped[engagement.centre.name if engagement and engagement.centre else 'No Department'] += amount
    return [{'name': name, 'total': total} for name, total in sorted(grouped.items(), key=lambda item: item[1], reverse=True)]


def get_top_clients_by_revenue(limit=5):
    grouped = defaultdict(lambda: ZERO)
    for _engagement, client, amount in revenue_by_engagement():
        grouped[client.name] += amount
    return [{'name': name, 'total': total} for name, total in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:limit]]


def get_pipeline_by_status():
    return (FinancialRecord.objects.filter(record_type=FinancialRecord.RecordType.PIPELINE)
            .values('engagement__status').annotate(total=Sum('amount')).order_by('-total'))
