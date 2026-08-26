from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inventory_view(request):
    return render(request, 'inventory/inventory.html')

