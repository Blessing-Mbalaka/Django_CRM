from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator

from apps.core.decorators import operational_required
from functionalities.engagements import services
from functionalities.ai.services import compute_churn_risk
from .forms import EngagementForm
from .models import Engagement


@login_required
def engagement_list(request):
    status = request.GET.get('status')
    centre = request.GET.get('department') or request.GET.get('centre')
    search = request.GET.get('q')
    qs = services.get_engagement_list(
        request.user, status=status, centre=centre, search=search
    )
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    # Pre-compute churn risk for all engagements on this page
    risk_scores = {e.pk: compute_churn_risk(e) for e in page_obj}
    return render(request, 'engagements/list.html', {
        'engagements': page_obj,
        'page_obj':    page_obj,
        'risk_scores': risk_scores,
        'status':      status or '',
        'search':      search or '',
    })


@login_required
def engagement_detail(request, pk):
    try:
        eng = services.get_engagement_detail(pk, request.user)
    except Engagement.DoesNotExist:
        raise Http404
    return render(request, 'engagements/detail.html', {'engagement': eng})


@login_required
@operational_required
def engagement_create(request):
    form = EngagementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        eng, duplicate = services.create_engagement(form, request.user)
        if duplicate:
            messages.warning(
                request,
                'Warning: an active/prospect engagement already exists for this '
                'client + department combination. Please review for overlap.'
            )
        messages.success(request, f'Engagement "{eng.title}" created.')
        return redirect('engagements:detail', pk=eng.pk)
    return render(request, 'engagements/form.html', {'form': form, 'action': 'Create'})


@login_required
@operational_required
def engagement_edit(request, pk):
    eng = get_object_or_404(Engagement, pk=pk)
    form = EngagementForm(request.POST or None, instance=eng)
    if request.method == 'POST' and form.is_valid():
        eng, duplicate = services.update_engagement(form, request.user)
        if duplicate:
            messages.warning(request, 'Overlap detected with another active/prospect engagement for this client + department.')
        messages.success(request, f'Engagement "{eng.title}" updated.')
        return redirect('engagements:detail', pk=eng.pk)
    return render(request, 'engagements/form.html', {'form': form, 'action': 'Edit', 'object': eng})


@login_required
@operational_required
def engagement_delete(request, pk):
    eng = get_object_or_404(Engagement, pk=pk)
    if request.method == 'POST':
        title = eng.title
        services.delete_engagement(eng)
        messages.success(request, f'Engagement "{title}" deleted.')
        return redirect('engagements:list')
    return render(request, 'confirm_delete.html', {
        'object': eng,
        'object_name': eng.title,
        'cancel_url': 'engagements:detail',
        'cancel_pk': eng.pk,
    })
