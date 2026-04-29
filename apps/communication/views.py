from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone

from functionalities.communication import services
from .forms import CommunicationLogForm


@login_required
def comms_health(request):
    context = services.get_comms_health_context()
    return render(request, 'communication/health.html', context)


@login_required
def log_contact(request):
    form = CommunicationLogForm(request.POST or None)
    if not form.data.get('contact_date'):
        form.initial['contact_date'] = timezone.now().date()
    if request.method == 'POST' and form.is_valid():
        engagement = form.cleaned_data['engagement']
        services.log_contact(
            engagement=engagement,
            user=request.user,
            contact_type=form.cleaned_data['contact_type'],
            summary=form.cleaned_data['summary'],
            contact_date=form.cleaned_data['contact_date'],
        )
        messages.success(request, 'Contact logged and engagement last-contact date updated.')
        return redirect('communication:health')
    return render(request, 'communication/log_form.html', {'form': form, 'action': 'Log Contact'})
