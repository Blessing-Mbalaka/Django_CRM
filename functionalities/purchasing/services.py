from django.core.exceptions import ValidationError
from django.db import transaction

from apps.products.models import Product
from decimal import Decimal

from apps.purchasing.models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseSequence, SupplierBill
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
def receive_purchase_order(*, purchase_order, received_on, user, reference='', line_quantities=None):
    purchase_order = PurchaseOrder.objects.select_for_update().prefetch_related('lines__product').get(pk=purchase_order.pk)
    if purchase_order.status not in (PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.PART_RECEIVED):
        raise ValidationError('Only approved or partially received purchase orders can be received.')
    receipt = GoodsReceipt.objects.create(purchase_order=purchase_order, received_on=received_on, reference=reference, received_by=user)
    requested = {int(key): Decimal(str(value)) for key, value in (line_quantities or {}).items()}
    order_line_ids = {line.id for line in purchase_order.lines.all()}
    if set(requested) - order_line_ids:
        raise ValidationError('Receipt contains a line from another purchase order.')
    received_any = False
    for line in purchase_order.lines.all():
        remaining = line.quantity - line.received_quantity
        quantity = requested.get(line.id, remaining if line_quantities is None else Decimal('0'))
        if quantity == 0:
            continue
        if quantity < 0 or quantity > remaining:
            raise ValidationError(f'Invalid receipt quantity for line {line.id}.')
        if line.product.product_type == Product.Type.STOCK:
            record_movement(product=line.product, location=purchase_order.location, movement_type='receipt', quantity=quantity, unit_cost=line.unit_cost, occurred_on=received_on, user=user, reference=purchase_order.number or '', source_type='goods_receipt', source_id=receipt.id)
        GoodsReceiptLine.objects.create(receipt=receipt, purchase_order_line=line, quantity=quantity)
        line.received_quantity += quantity
        line.save(update_fields=['received_quantity'])
        received_any = True
    if not received_any:
        raise ValidationError('At least one receipt quantity is required.')
    fully_received = all(line.received_quantity == line.quantity for line in purchase_order.lines.all())
    purchase_order.status = PurchaseOrder.Status.RECEIVED if fully_received else PurchaseOrder.Status.PART_RECEIVED
    purchase_order.save(update_fields=['status', 'updated_at'])
    return receipt


@transaction.atomic
def create_supplier_bill(*, purchase_order, supplier_invoice_number, due_date, user, bill_date):
    purchase_order = PurchaseOrder.objects.select_for_update().prefetch_related('lines__product').get(pk=purchase_order.pk)
    if purchase_order.status != PurchaseOrder.Status.RECEIVED:
        raise ValidationError('Supplier bills can only be created for fully received purchase orders.')
    if SupplierBill.objects.filter(purchase_order=purchase_order).exists():
        raise ValidationError('This purchase order already has a supplier bill.')
    subtotal = sum((line.line_total for line in purchase_order.lines.all()), Decimal('0.00'))
    tax_total = sum(((line.line_total * line.tax_rate / Decimal('100')).quantize(Decimal('0.01')) for line in purchase_order.lines.all()), Decimal('0.00'))
    return SupplierBill.objects.create(purchase_order=purchase_order, supplier_invoice_number=supplier_invoice_number, bill_date=bill_date, due_date=due_date, subtotal=subtotal, tax_total=tax_total, total=subtotal + tax_total, created_by=user)


@transaction.atomic
def post_supplier_bill(*, supplier_bill):
    supplier_bill = SupplierBill.objects.select_for_update().select_related('purchase_order').get(pk=supplier_bill.pk)
    if supplier_bill.status != SupplierBill.Status.DRAFT:
        raise ValidationError('Only draft supplier bills can be posted.')
    from functionalities.accounting.posting import post_supplier_bill as create_posting
    journal = create_posting(supplier_bill)
    if journal is None:
        raise ValidationError('Configure supplier-bill system accounts before posting.')
    supplier_bill.status = SupplierBill.Status.POSTED
    supplier_bill.journal_entry = journal
    supplier_bill.save(update_fields=['status', 'journal_entry'])
    return supplier_bill
