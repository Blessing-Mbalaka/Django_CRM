from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from apps.core.decorators import exec_required
from functionalities.centres import services
from .forms import CentreForm
from .models import Centre


@login_required
def centre_list(request):
    centres = services.get_all_centres_summary()
    return render(request, 'centres/list.html', {'centres': centres})


@login_required
def centre_detail(request, pk):
    try:
        context = services.get_centre_detail_context(pk)
    except Centre.DoesNotExist:
        raise Http404
    return render(request, 'centres/detail.html', context)


@login_required
@exec_required
def centre_create(request):
    form = CentreForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        centre = form.save()
        messages.success(request, f'Department "{centre.name}" created.')
        return redirect('centres:detail', pk=centre.pk)
    return render(request, 'centres/form.html', {'form': form, 'action': 'Create'})


@login_required
@exec_required
def centre_edit(request, pk):
    centre = get_object_or_404(Centre, pk=pk)
    form = CentreForm(request.POST or None, instance=centre)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Department "{centre.name}" updated.')
        return redirect('centres:detail', pk=centre.pk)
    return render(request, 'centres/form.html', {'form': form, 'action': 'Edit', 'object': centre})


@login_required
@exec_required
def centre_delete(request, pk):
    centre = get_object_or_404(Centre, pk=pk)
    if request.method == 'POST':
        name = centre.name
        centre.delete()
        messages.success(request, f'Department "{name}" deleted.')
        return redirect('centres:list')
    return render(request, 'confirm_delete.html', {
        'object': centre,
        'object_name': centre.name,
        'cancel_url': 'centres:detail',
        'cancel_pk': centre.pk,
    })
