from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator

from apps.core.decorators import operational_required
from functionalities.alerts import services
from functionalities.ai.services import run_ai_alert_pipeline
from .forms import AlertForm
from .models import Alert


@login_required
def alert_list(request):
    severity = request.GET.get('severity')
    alert_type = request.GET.get('alert_type')
    qs = services.get_active_alerts(severity=severity, alert_type=alert_type)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'alerts/list.html', {
        'alerts':      page_obj,
        'page_obj':    page_obj,
        'severity':    severity or '',
        'alert_type':  alert_type or '',
    })


@login_required
def alert_detail(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    return render(request, 'alerts/detail.html', {'alert': alert})


@login_required
@operational_required
def alert_create(request):
    form = AlertForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        alert = form.save()
        messages.success(request, f'Alert "{alert.title}" created.')
        return redirect('alerts:list')
    return render(request, 'alerts/form.html', {'form': form, 'action': 'Create'})


@login_required
@operational_required
def alert_edit(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    form = AlertForm(request.POST or None, instance=alert)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Alert "{alert.title}" updated.')
        return redirect('alerts:list')
    return render(request, 'alerts/form.html', {'form': form, 'action': 'Edit', 'object': alert})


@login_required
@operational_required
def alert_delete(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        title = alert.title
        alert.delete()
        messages.success(request, f'Alert "{title}" deleted.')
        return redirect('alerts:list')
    return render(request, 'confirm_delete.html', {
        'object': alert,
        'object_name': alert.title,
        'cancel_url': 'alerts:list',
        'cancel_pk': None,
    })


@login_required
def alert_resolve(request, pk):
    """POST-only: mark alert as resolved."""
    if request.method == 'POST':
        services.resolve_alert(pk)
        messages.success(request, 'Alert marked as resolved.')
    return redirect('alerts:list')


@login_required
def run_alert_pipeline(request):
    """POST-only: trigger rule-based + AI alert generation pipeline."""
    if request.method != 'POST':
        return redirect('alerts:list')
    # Rule-based pipeline
    summary = services.run_alert_pipeline()
    rule_total = sum(summary.values())
    # AI pipeline
    ai_summary = run_ai_alert_pipeline()
    ai_total = ai_summary['churn_created'] + ai_summary['dormancy_created']
    total = rule_total + ai_total
    messages.success(
        request,
        f'Alert pipeline complete. {rule_total} rule-based + {ai_total} AI alert(s) generated ({total} total).'
    )
    return redirect('alerts:list')
