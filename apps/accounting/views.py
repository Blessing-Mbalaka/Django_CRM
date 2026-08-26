from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def ledger_view(request):
    return render(request, 'accounting/ledger.html')

