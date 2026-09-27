from collections import defaultdict
from decimal import Decimal

from apps.inventory.models import StockMovement
from .queries import inventory_summary, product_stock_rows


REPORT_NAMES = (
    'Current Stock Summary', 'Inventory Value', 'Low Stock Report',
    'Out of Stock Report', 'Stock Movement Summary', 'Products by Category',
)


def safe_csv_cell(value):
    text = str(value)
    return "'" + text if text.startswith(('=', '+', '-', '@')) else text


def report_dataset(name):
    if name not in REPORT_NAMES:
        raise ValueError('Unknown inventory report.')
    products = product_stock_rows()
    summary = inventory_summary()
    if name == 'Stock Movement Summary':
        grouped = defaultdict(lambda: {'count': 0, 'in': Decimal('0'), 'out': Decimal('0')})
        for movement in StockMovement.objects.all():
            label = movement.get_movement_type_display()
            grouped[label]['count'] += 1
            grouped[label]['out' if movement.signed_quantity < 0 else 'in'] += abs(movement.signed_quantity)
        rows = [[label, values['count'], values['in'], values['out']] for label, values in sorted(grouped.items())]
        return {'name': name, 'headers': ['Movement', 'Transactions', 'Units In', 'Units Out'], 'rows': rows, 'summary': summary}
    if name == 'Products by Category':
        grouped = defaultdict(lambda: {'products': 0, 'units': Decimal('0'), 'value': Decimal('0')})
        for product in products:
            values = grouped[product['category_name']]
            values['products'] += 1
            values['units'] += product['quantity']
            values['value'] += product['inventory_value']
        rows = [[category, values['products'], values['units'], values['value']] for category, values in sorted(grouped.items())]
        return {'name': name, 'headers': ['Category', 'Products', 'Units', 'Value'], 'rows': rows, 'summary': summary}
    if name == 'Low Stock Report':
        products = [product for product in products if product['status'] == 'Low Stock']
    elif name == 'Out of Stock Report':
        products = [product for product in products if product['status'] == 'Out of Stock']
    headers = ['Product', 'SKU', 'Category', 'Quantity', 'Unit', 'Minimum', 'Status', 'Cost', 'Inventory Value', 'Supplier']
    rows = [[product[key] for key in ('name', 'sku', 'category_name', 'quantity', 'unit', 'minimum', 'status', 'cost_price', 'inventory_value', 'supplier_name')] for product in products]
    return {'name': name, 'headers': headers, 'rows': rows, 'summary': summary}
