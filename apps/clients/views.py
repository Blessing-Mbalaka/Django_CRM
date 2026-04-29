from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404

from apps.core.decorators import operational_required
from functionalities.clients import services
from functionalities.ai.services import compute_dormancy_risk
from .forms import ClientForm
from .models import Client


@login_required
def client_list(request):
    search = request.GET.get('q')
    sector = request.GET.get('sector')
    centre = request.GET.get('centre')
    clients_qs = services.get_client_list(request.user, search=search, sector=sector, centre=centre)

    from .models import Client
    from apps.centres.models import Centre as CentreModel
    paginator = Paginator(clients_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'clients/list.html', {
        'clients':        page_obj,
        'page_obj':       page_obj,
        'search':         search or '',
        'sector':         sector or '',
        'centre_filter':  centre or '',
        'sector_choices': Client.Sector.choices,
        'centres':        CentreModel.objects.filter(is_active=True).order_by('name'),
    })


@login_required
def client_detail(request, pk):
    try:
        client = services.get_client_detail(pk, request.user)
    except Client.DoesNotExist:
        raise Http404
    engagements = client.engagements.select_related('lead_owner').order_by('-updated_at')
    dormancy_risk = compute_dormancy_risk(client)
    return render(request, 'clients/detail.html', {
        'client': client,
        'engagements': engagements,
        'dormancy_risk': dormancy_risk,
    })


@login_required
@operational_required
def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = services.create_client(form, request.user)
        messages.success(request, f'Client "{client.name}" created successfully.')
        return redirect('clients:detail', pk=client.pk)
    return render(request, 'clients/form.html', {'form': form, 'action': 'Create'})


@login_required
@operational_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        services.update_client(form)
        messages.success(request, f'Client "{client.name}" updated.')
        return redirect('clients:detail', pk=client.pk)
    return render(request, 'clients/form.html', {'form': form, 'action': 'Edit', 'object': client})


@login_required
@operational_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        name = client.name
        services.delete_client(client)
        messages.success(request, f'Client "{name}" deleted.')
        return redirect('clients:list')
    return render(request, 'confirm_delete.html', {
        'object': client,
        'object_name': client.name,
        'cancel_url': 'clients:detail',
        'cancel_pk': client.pk,
    })
