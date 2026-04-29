from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from apps.core.decorators import management_required
from functionalities.finance import services
from .forms import FinancialRecordForm
from .models import FinancialRecord


@login_required
def finance_overview(request):
    context = services.get_finance_overview()
    context['centre_breakdown'] = services.get_centre_revenue_breakdown()
    context['top_clients'] = services.get_top_clients_by_revenue(limit=5)
    context['pipeline_by_status'] = services.get_pipeline_by_status()
    return render(request, 'finance/overview.html', context)


@login_required
@management_required
def finance_create(request):
    form = FinancialRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save()
        messages.success(request, f'Financial record added (R{record.amount}).')
        return redirect('finance:overview')
    return render(request, 'finance/form.html', {'form': form, 'action': 'Add'})


@login_required
@management_required
def finance_edit(request, pk):
    record = get_object_or_404(FinancialRecord, pk=pk)
    form = FinancialRecordForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Financial record updated.')
        return redirect('finance:overview')
    return render(request, 'finance/form.html', {'form': form, 'action': 'Edit', 'object': record})


@login_required
@management_required
def finance_delete(request, pk):
    record = get_object_or_404(FinancialRecord, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Financial record deleted.')
        return redirect('finance:overview')
    return render(request, 'confirm_delete.html', {
        'object': record,
        'object_name': str(record),
        'cancel_url': 'finance:overview',
        'cancel_pk': None,
    })
