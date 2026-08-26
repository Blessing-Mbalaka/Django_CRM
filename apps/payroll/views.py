from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.decorators import exec_required


@login_required
@exec_required
def payroll_view(request):
    return render(request, 'payroll/payroll.html')
