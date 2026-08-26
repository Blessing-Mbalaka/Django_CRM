from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from apps.accounting.models import Account, JournalEntry, JournalLine


REPORTABLE_STATUSES = (JournalEntry.Status.POSTED, JournalEntry.Status.REVERSED)
ZERO = Decimal('0.00')


def parse_report_date(value, field_name):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError({field_name: 'Use a valid date in YYYY-MM-DD format.'})


def account_activity(*, end_date, start_date=None):
    filters = Q(journal_lines__entry__status__in=REPORTABLE_STATUSES, journal_lines__entry__date__lte=end_date)
    if start_date:
        filters &= Q(journal_lines__entry__date__gte=start_date)
    return Account.objects.annotate(
        report_debit=Coalesce(Sum('journal_lines__debit', filter=filters), ZERO),
        report_credit=Coalesce(Sum('journal_lines__credit', filter=filters), ZERO),
    ).order_by('code')


def trial_balance(*, as_of):
    as_of = parse_report_date(as_of, 'as_of')
    rows, total_debit, total_credit = [], ZERO, ZERO
    for account in account_activity(end_date=as_of):
        balance = account.report_debit - account.report_credit
        debit, credit = (balance, ZERO) if balance >= 0 else (ZERO, -balance)
        if debit or credit:
            rows.append({'account': account.id, 'code': account.code, 'name': account.name, 'account_type': account.account_type, 'debit': debit, 'credit': credit})
            total_debit += debit
            total_credit += credit
    return {'as_of': as_of, 'rows': rows, 'total_debit': total_debit, 'total_credit': total_credit, 'is_balanced': total_debit == total_credit}


def income_statement(*, start_date, end_date):
    start_date = parse_report_date(start_date, 'start_date')
    end_date = parse_report_date(end_date, 'end_date')
    if end_date < start_date:
        raise ValidationError({'end_date': 'End date cannot precede start date.'})
    revenue, expenses = [], []
    for account in account_activity(start_date=start_date, end_date=end_date).filter(account_type__in=[Account.Type.REVENUE, Account.Type.EXPENSE]):
        amount = account.report_credit - account.report_debit if account.account_type == Account.Type.REVENUE else account.report_debit - account.report_credit
        if amount:
            target = revenue if account.account_type == Account.Type.REVENUE else expenses
            target.append({'account': account.id, 'code': account.code, 'name': account.name, 'amount': amount})
    total_revenue = sum((row['amount'] for row in revenue), ZERO)
    total_expenses = sum((row['amount'] for row in expenses), ZERO)
    return {'start_date': start_date, 'end_date': end_date, 'revenue': revenue, 'expenses': expenses, 'total_revenue': total_revenue, 'total_expenses': total_expenses, 'net_profit': total_revenue - total_expenses}


def balance_sheet(*, as_of):
    as_of = parse_report_date(as_of, 'as_of')
    groups = {'assets': [], 'liabilities': [], 'equity': []}
    earnings = ZERO
    for account in account_activity(end_date=as_of):
        if account.account_type == Account.Type.ASSET:
            amount = account.report_debit - account.report_credit
            target = 'assets'
        elif account.account_type in (Account.Type.LIABILITY, Account.Type.EQUITY):
            amount = account.report_credit - account.report_debit
            target = 'liabilities' if account.account_type == Account.Type.LIABILITY else 'equity'
        elif account.account_type == Account.Type.REVENUE:
            earnings += account.report_credit - account.report_debit
            continue
        else:
            earnings -= account.report_debit - account.report_credit
            continue
        if amount:
            groups[target].append({'account': account.id, 'code': account.code, 'name': account.name, 'amount': amount})
    groups['equity'].append({'account': None, 'code': '', 'name': 'Current retained earnings', 'amount': earnings})
    total_assets = sum((row['amount'] for row in groups['assets']), ZERO)
    total_liabilities = sum((row['amount'] for row in groups['liabilities']), ZERO)
    total_equity = sum((row['amount'] for row in groups['equity']), ZERO)
    return {'as_of': as_of, **groups, 'total_assets': total_assets, 'total_liabilities': total_liabilities, 'total_equity': total_equity, 'is_balanced': total_assets == total_liabilities + total_equity}
