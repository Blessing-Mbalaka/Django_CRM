from django.core.exceptions import ValidationError
from django.db import transaction

from apps.billing.models import Invoice, InvoiceLine
from apps.products.models import Product
from apps.sales.models import Fulfilment, SalesOrder, SalesSequence
from functionalities.billing.services import issue_invoice
from functionalities.inventory.services import record_movement


@transaction.atomic
def confirm_sales_order(*, sales_order):
    sales_order = SalesOrder.objects.select_for_update().get(pk=sales_order.pk)
    if sales_order.status != SalesOrder.Status.DRAFT:
        raise ValidationError('Only draft sales orders can be confirmed.')
    if not sales_order.lines.exists():
        raise ValidationError('A sales order needs at least one line.')
    stock_lines = sales_order.lines.filter(product__product_type=Product.Type.STOCK)
    if stock_lines.exists() and not sales_order.location_id:
        raise ValidationError('A stock location is required for stock products.')
    sequence, _ = SalesSequence.objects.select_for_update().get_or_create(key='sales_order')
    sales_order.number = f'{sequence.prefix}-{sequence.next_number:06d}'
    sequence.next_number += 1
    sequence.save(update_fields=['next_number'])
    sales_order.status = SalesOrder.Status.CONFIRMED
    sales_order.save(update_fields=['number', 'status', 'updated_at'])
    return sales_order


@transaction.atomic
def fulfil_sales_order(*, sales_order, fulfilled_on, user, reference=''):
    sales_order = SalesOrder.objects.select_for_update().prefetch_related('lines__product').get(pk=sales_order.pk)
    if sales_order.status != SalesOrder.Status.CONFIRMED:
        raise ValidationError('Only confirmed sales orders can be fulfilled.')
    for line in sales_order.lines.all():
        if line.product.product_type == Product.Type.STOCK:
            record_movement(product=line.product, location=sales_order.location, movement_type='issue', quantity=line.quantity, occurred_on=fulfilled_on, user=user, reference=sales_order.number or '', source_type='sales_order', source_id=sales_order.id)
    fulfilment = Fulfilment.objects.create(sales_order=sales_order, fulfilled_on=fulfilled_on, reference=reference, fulfilled_by=user)
    sales_order.status = SalesOrder.Status.FULFILLED
    sales_order.save(update_fields=['status', 'updated_at'])
    return fulfilment


@transaction.atomic
def invoice_sales_order(*, sales_order, due_date, user):
    sales_order = SalesOrder.objects.select_for_update().prefetch_related('lines__product').get(pk=sales_order.pk)
    if sales_order.status not in (SalesOrder.Status.CONFIRMED, SalesOrder.Status.FULFILLED):
        raise ValidationError('Only confirmed or fulfilled sales orders can be invoiced.')
    if sales_order.invoice_id:
        raise ValidationError('This sales order already has an invoice.')
    invoice = Invoice.objects.create(client=sales_order.client, engagement=sales_order.engagement, issue_date=sales_order.order_date, due_date=due_date, notes=f'Created from {sales_order.number}', created_by=user)
    for line in sales_order.lines.all():
        InvoiceLine.objects.create(invoice=invoice, description=line.description or line.product.name, quantity=line.quantity, unit_price=line.unit_price, tax_rate=line.tax_rate)
    invoice = issue_invoice(invoice=invoice)
    sales_order.invoice = invoice
    sales_order.save(update_fields=['invoice', 'updated_at'])
    return invoice
