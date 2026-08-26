from django.core.exceptions import ValidationError
from django.db import transaction

from apps.products.models import Product
from apps.purchasing.models import GoodsReceipt, PurchaseOrder, PurchaseSequence
from functionalities.inventory.services import record_movement


@transaction.atomic
def approve_purchase_order(*, purchase_order):
    purchase_order = PurchaseOrder.objects.select_for_update().get(pk=purchase_order.pk)
    if purchase_order.status != PurchaseOrder.Status.DRAFT:
        raise ValidationError('Only draft purchase orders can be approved.')
    if not purchase_order.lines.exists():
        raise ValidationError('A purchase order needs at least one line.')
    sequence, _ = PurchaseSequence.objects.select_for_update().get_or_create(key='purchase_order')
    purchase_order.number = f'{sequence.prefix}-{sequence.next_number:06d}'
    sequence.next_number += 1
    sequence.save(update_fields=['next_number'])
    purchase_order.status = PurchaseOrder.Status.APPROVED
    purchase_order.save(update_fields=['number', 'status', 'updated_at'])
    return purchase_order


@transaction.atomic
def receive_purchase_order(*, purchase_order, received_on, user, reference=''):
    purchase_order = PurchaseOrder.objects.select_for_update().prefetch_related('lines__product').get(pk=purchase_order.pk)
    if purchase_order.status != PurchaseOrder.Status.APPROVED:
        raise ValidationError('Only approved purchase orders can be received.')
    receipt = GoodsReceipt.objects.create(purchase_order=purchase_order, received_on=received_on, reference=reference, received_by=user)
    for line in purchase_order.lines.all():
        if line.product.product_type == Product.Type.STOCK:
            record_movement(product=line.product, location=purchase_order.location, movement_type='receipt', quantity=line.quantity, unit_cost=line.unit_cost, occurred_on=received_on, user=user, reference=purchase_order.number or '', source_type='purchase_order', source_id=purchase_order.id)
        line.received_quantity = line.quantity
        line.save(update_fields=['received_quantity'])
    purchase_order.status = PurchaseOrder.Status.RECEIVED
    purchase_order.save(update_fields=['status', 'updated_at'])
    return receipt

