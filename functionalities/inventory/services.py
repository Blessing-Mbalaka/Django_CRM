from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When

from apps.inventory.models import StockMovement
from apps.products.models import Product


def stock_on_hand(*, product, location):
    result = StockMovement.objects.filter(product=product, location=location).aggregate(
        quantity=Sum(Case(
            When(movement_type__in=[StockMovement.Type.ISSUE, StockMovement.Type.ADJUSTMENT_OUT], then=-F('quantity')),
            default=F('quantity'),
            output_field=DecimalField(max_digits=18, decimal_places=3),
        ))
    )['quantity']
    return result or Decimal('0.000')


@transaction.atomic
def record_movement(*, product, location, movement_type, quantity, occurred_on, user, unit_cost=0, reference='', source_type='', source_id=None):
    product = Product.objects.select_for_update().get(pk=product.pk)
    quantity = Decimal(str(quantity))
    if product.product_type != Product.Type.STOCK:
        raise ValidationError('Stock movements can only be recorded for stock products.')
    if quantity <= 0:
        raise ValidationError('Movement quantity must be greater than zero.')
    if movement_type in (StockMovement.Type.ISSUE, StockMovement.Type.ADJUSTMENT_OUT) and stock_on_hand(product=product, location=location) < quantity:
        raise ValidationError('Insufficient stock at this location.')
    return StockMovement.objects.create(product=product, location=location, movement_type=movement_type, quantity=quantity, unit_cost=unit_cost, occurred_on=occurred_on, reference=reference, source_type=source_type, source_id=source_id, created_by=user)

