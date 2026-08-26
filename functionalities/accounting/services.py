from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounting.models import AccountingPeriod, JournalEntry, JournalLine
from .validators import validate_line_amounts, validate_period_is_open


@transaction.atomic
def create_draft_entry(*, date, description, lines, user, reference='', source_type='', source_id=None):
    if len(lines) < 2:
        raise ValidationError('A journal entry requires at least two lines.')
    entry = JournalEntry.objects.create(date=date, description=description, reference=reference, source_type=source_type, source_id=source_id, created_by=user)
    for line in lines:
        debit = Decimal(str(line.get('debit', 0)))
        credit = Decimal(str(line.get('credit', 0)))
        validate_line_amounts(debit=debit, credit=credit)
        JournalLine.objects.create(entry=entry, account=line['account'], description=line.get('description', ''), debit=debit, credit=credit)
    return entry


@transaction.atomic
def post_entry(*, entry):
    entry = JournalEntry.objects.select_for_update().prefetch_related('lines').get(pk=entry.pk)
    if entry.status != JournalEntry.Status.DRAFT:
        raise ValidationError('Only draft journal entries can be posted.')
    validate_period_is_open(entry_date=entry.date, periods=AccountingPeriod.objects.all())
    if entry.lines.count() < 2 or entry.total_debit <= 0 or entry.total_debit != entry.total_credit:
        raise ValidationError('Journal entry debits and credits must balance and be greater than zero.')
    entry.status = JournalEntry.Status.POSTED
    entry.posted_at = timezone.now()
    entry.save(update_fields=['status', 'posted_at'])
    return entry


@transaction.atomic
def reverse_entry(*, entry, reversal_date, user, description=''):
    entry = JournalEntry.objects.select_for_update().prefetch_related('lines').get(pk=entry.pk)
    if entry.status != JournalEntry.Status.POSTED:
        raise ValidationError('Only posted journal entries can be reversed.')
    reversal = create_draft_entry(
        date=reversal_date,
        reference=f'REV-{entry.reference or entry.pk}',
        description=description or f'Reversal of {entry.description}',
        source_type='journal_reversal',
        source_id=entry.id,
        user=user,
        lines=[{'account': line.account, 'description': line.description, 'debit': line.credit, 'credit': line.debit} for line in entry.lines.all()],
    )
    reversal.reversal_of = entry
    reversal.save(update_fields=['reversal_of'])
    reversal = post_entry(entry=reversal)
    entry.status = JournalEntry.Status.REVERSED
    entry.save(update_fields=['status'])
    return reversal
