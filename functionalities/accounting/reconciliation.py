from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounting.models import Account, BankStatement, BankStatementLine, JournalEntry, JournalLine


@transaction.atomic
def create_bank_statement(*, bank_account, reference, start_date, end_date, opening_balance, closing_balance, lines, user):
    if bank_account.system_role != Account.SystemRole.BANK:
        raise ValidationError({'bank_account': 'Statements require an account with the Bank / Cash system role.'})
    if end_date < start_date:
        raise ValidationError({'end_date': 'End date cannot precede start date.'})
    opening_balance = Decimal(str(opening_balance))
    closing_balance = Decimal(str(closing_balance))
    movement = sum((Decimal(str(line['amount'])) for line in lines), Decimal('0.00'))
    if opening_balance + movement != closing_balance:
        raise ValidationError({'closing_balance': 'Opening balance plus statement transactions must equal the closing balance.'})
    statement = BankStatement.objects.create(bank_account=bank_account, reference=reference, start_date=start_date, end_date=end_date, opening_balance=opening_balance, closing_balance=closing_balance, created_by=user)
    for line in lines:
        transaction_date = line['transaction_date']
        if transaction_date < start_date or transaction_date > end_date:
            raise ValidationError({'lines': 'Every transaction date must fall inside the statement period.'})
        BankStatementLine.objects.create(statement=statement, transaction_date=transaction_date, description=line['description'], reference=line.get('reference', ''), amount=line['amount'])
    return statement


def reconciliation_candidates(*, statement_line):
    candidates = JournalLine.objects.filter(
        account=statement_line.statement.bank_account,
        entry__status__in=[JournalEntry.Status.POSTED, JournalEntry.Status.REVERSED],
        entry__date__range=(statement_line.statement.start_date, statement_line.statement.end_date),
        bank_statement_match__isnull=True,
    )
    if statement_line.amount >= 0:
        candidates = candidates.filter(debit=statement_line.amount, credit=0)
    else:
        candidates = candidates.filter(debit=0, credit=-statement_line.amount)
    return candidates.select_related('entry', 'account').order_by('entry__date', 'id')


@transaction.atomic
def reconcile_statement_line(*, statement_line, journal_line, user):
    statement_line = BankStatementLine.objects.select_for_update().select_related('statement__bank_account').get(pk=statement_line.pk)
    journal_line = JournalLine.objects.select_for_update().select_related('entry').get(pk=journal_line.pk)
    if statement_line.is_reconciled:
        raise ValidationError('This bank statement line is already reconciled.')
    if journal_line.account_id != statement_line.statement.bank_account_id:
        raise ValidationError('The journal line does not use this statement bank account.')
    if journal_line.entry.status not in (JournalEntry.Status.POSTED, JournalEntry.Status.REVERSED):
        raise ValidationError('Only posted journal lines can be reconciled.')
    if hasattr(journal_line, 'bank_statement_match'):
        raise ValidationError('This journal line is already reconciled.')
    ledger_amount = journal_line.debit - journal_line.credit
    if ledger_amount != statement_line.amount:
        raise ValidationError('The bank statement and journal line amounts must match.')
    statement_line.matched_journal_line = journal_line
    statement_line.reconciled_by = user
    statement_line.reconciled_at = timezone.now()
    statement_line.save(update_fields=['matched_journal_line', 'reconciled_by', 'reconciled_at'])
    statement = statement_line.statement
    if not statement.lines.filter(matched_journal_line__isnull=True).exists():
        statement.status = BankStatement.Status.RECONCILED
        statement.save(update_fields=['status'])
    return statement_line


@transaction.atomic
def unreconcile_statement_line(*, statement_line):
    statement_line = BankStatementLine.objects.select_for_update().select_related('statement').get(pk=statement_line.pk)
    if not statement_line.is_reconciled:
        raise ValidationError('This bank statement line is not reconciled.')
    statement_line.matched_journal_line = None
    statement_line.reconciled_by = None
    statement_line.reconciled_at = None
    statement_line.save(update_fields=['matched_journal_line', 'reconciled_by', 'reconciled_at'])
    if statement_line.statement.status == BankStatement.Status.RECONCILED:
        statement_line.statement.status = BankStatement.Status.OPEN
        statement_line.statement.save(update_fields=['status'])
    return statement_line
