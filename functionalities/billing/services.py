from django.db import transaction

from apps.billing.models import Invoice, NumberSequence, Payment
from .validators import validate_payment


@transaction.atomic
def issue_invoice(*, invoice):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status != Invoice.Status.DRAFT:
        return invoice
    if not invoice.lines.exists():
        raise ValueError('An invoice needs at least one line before it can be issued.')
    sequence, _ = NumberSequence.objects.select_for_update().get_or_create(key='invoice', defaults={'prefix': 'INV'})
    invoice.number = f'{sequence.prefix}-{sequence.next_number:06d}'
    sequence.next_number += 1
    sequence.save(update_fields=['next_number'])
    invoice.status = Invoice.Status.ISSUED
    invoice.save(update_fields=['number', 'status', 'updated_at'])
    return invoice


@transaction.atomic
def record_payment(*, invoice, amount, paid_on, user, reference=''):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    validate_payment(invoice=invoice, amount=amount)
    payment = Payment.objects.create(invoice=invoice, amount=amount, paid_on=paid_on, reference=reference, recorded_by=user)
    invoice.status = Invoice.Status.PAID if invoice.balance_due == 0 else Invoice.Status.PART_PAID
    invoice.save(update_fields=['status', 'updated_at'])
    return payment
