from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required
def inventory_view(request):
    can_manage = request.user.is_superuser or request.user.role in ('dean', 'director', 'admin')
    config = {
        'user': {'id': request.user.id, 'name': request.user.get_full_name() or request.user.username, 'can_manage': can_manage},
        'urls': {
            'workspace': reverse('inventory-workspace-list'),
            'summary': reverse('inventory-workspace-summary'),
            'stock_rows': reverse('inventory-workspace-products'),
            'low_stock': reverse('inventory-workspace-low-stock'),
            'reports': reverse('inventory-workspace-reports'),
            'report_csv': reverse('inventory-workspace-report-csv'),
            'backup': reverse('inventory-workspace-backup'),
            'clear_data': reverse('inventory-workspace-clear-data'),
            'products': reverse('inventory-product-list'),
            'categories': reverse('inventory-category-list'),
            'settings': reverse('inventory-settings-list'),
            'suppliers': reverse('supplier-list'),
            'locations': reverse('stock-location-list'),
            'movements': reverse('stock-movement-list'),
            'rules': reverse('reorder-rule-list'),
        },
    }
    return render(request, 'inventory/inventory.html', {'inventory_workspace_config': config})

