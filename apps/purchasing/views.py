from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def purchase_orders_view(request):
    return render(request, 'purchasing/orders.html')

