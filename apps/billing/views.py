from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def invoice_view(request):
    return render(request, 'billing/invoices.html')

