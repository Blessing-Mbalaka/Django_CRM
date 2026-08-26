from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def expense_view(request):
    return render(request, 'expenses/expenses.html')

