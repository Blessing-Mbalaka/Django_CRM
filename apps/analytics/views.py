from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from functionalities.analytics import services


@login_required
def reports_view(request):
    context = services.get_reports_context()
    from apps.inventory.models import StockLocation
    from apps.products.models import Product
    from apps.purchasing.models import Supplier
    context.update({
        'activity_products': Product.objects.filter(is_active=True).order_by('name'),
        'activity_locations': StockLocation.objects.filter(is_active=True).order_by('name'),
        'activity_suppliers': Supplier.objects.filter(is_active=True).order_by('name'),
    })
    return render(request, 'analytics/reports.html', context)
