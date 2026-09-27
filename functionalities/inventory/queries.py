from decimal import Decimal

from django.db.models import Case, DecimalField, F, Q, Sum, Value, When

from apps.inventory.models import InventorySettings, ProductInventoryProfile, ReorderRule, StockMovement
from apps.products.models import Product


SIGNED_QUANTITY = Sum(Case(
    When(stock_movements__movement_type__in=[StockMovement.Type.ISSUE, StockMovement.Type.ADJUSTMENT_OUT], then=-F('stock_movements__quantity')),
    default=F('stock_movements__quantity'),
    output_field=DecimalField(max_digits=18, decimal_places=3),
), default=Value(Decimal('0.000')))


def product_stock_rows(queryset=None):
    settings = InventorySettings.load()
    products = queryset if queryset is not None else Product.objects.filter(is_active=True, product_type=Product.Type.STOCK)
    products = products.select_related('inventory_profile__category', 'inventory_profile__preferred_supplier').annotate(on_hand=SIGNED_QUANTITY)
    rows = []
    for product in products:
        try:
            profile = product.inventory_profile
        except ProductInventoryProfile.DoesNotExist:
            profile = None
        rules = list(ReorderRule.objects.filter(product=product).select_related('location'))
        minimum = max((rule.minimum_quantity for rule in rules), default=settings.default_reorder_level)
        quantity = product.on_hand or Decimal('0.000')
        status = 'Out of Stock' if quantity <= 0 else ('Low Stock' if quantity <= minimum else 'In Stock')
        unit = profile.unit if profile else settings.default_unit
        supplier = profile.preferred_supplier if profile else None
        category = profile.category if profile else None
        rows.append({
            'id': product.id, 'name': product.name, 'sku': product.sku,
            'description': product.description, 'cost_price': product.cost_price,
            'sales_price': product.sales_price, 'quantity': quantity, 'unit': unit,
            'minimum': minimum, 'status': status,
            'category': category.id if category else None,
            'category_name': category.name if category else 'Uncategorised',
            'preferred_supplier': supplier.id if supplier else None,
            'supplier_name': supplier.name if supplier else 'Not assigned',
            'stock_reference': profile.stock_reference if profile else '',
            'inventory_value': (quantity * product.cost_price).quantize(Decimal('0.01')),
        })
    return rows


def low_stock_rows():
    return [row for row in product_stock_rows() if row['status'] != 'In Stock']


def inventory_summary():
    rows = product_stock_rows()
    units = sum((row['quantity'] for row in rows), Decimal('0.000'))
    value = sum((row['inventory_value'] for row in rows), Decimal('0.00'))
    units_used = sorted({row['unit'] for row in rows if row['quantity']})
    return {
        'products': len(rows), 'aggregate_quantity': units,
        'quantity_label': 'Aggregate quantity' if len(units_used) > 1 else (units_used[0] if units_used else InventorySettings.load().default_unit),
        'inventory_value': value,
        'low_stock': sum(row['status'] == 'Low Stock' for row in rows),
        'out_of_stock': sum(row['status'] == 'Out of Stock' for row in rows),
        'status_distribution': {status: sum(row['status'] == status for row in rows) for status in ('In Stock', 'Low Stock', 'Out of Stock')},
        'recent_movements': movement_history()[:5],
    }


def movement_history(filters=None):
    filters = filters or {}
    qs = StockMovement.objects.select_related('product', 'location', 'created_by')
    if filters.get('product'):
        qs = qs.filter(product_id=filters['product'])
    if filters.get('location'):
        qs = qs.filter(location_id=filters['location'])
    if filters.get('movement_type'):
        qs = qs.filter(movement_type=filters['movement_type'])
    if filters.get('from'):
        qs = qs.filter(occurred_on__gte=filters['from'])
    if filters.get('to'):
        qs = qs.filter(occurred_on__lte=filters['to'])
    if filters.get('q'):
        qs = qs.filter(Q(product__name__icontains=filters['q']) | Q(product__sku__icontains=filters['q']) | Q(reference__icontains=filters['q']))
    return qs
