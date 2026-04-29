from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.crypto import get_random_string

from apps.core.decorators import management_required
from apps.centres.models import Centre
from functionalities.people import services
from apps.accounts.models import User
from apps.staff.models import StaffProfile
from .forms import StaffProfileForm


@login_required
def staff_list(request):
    centre_id = request.GET.get('centre')
    search = request.GET.get('q')
    qs = services.get_staff_directory(centre_id=centre_id, search=search)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'staff/list.html', {
        'staff':          page_obj,
        'page_obj':       page_obj,
        'search':         search or '',
        'centre_filter':  centre_id or '',
        'centres':        Centre.objects.filter(is_active=True).order_by('name'),
    })


@login_required
def staff_detail(request, pk):
    member = get_object_or_404(User, pk=pk)
    return render(request, 'staff/detail.html', {'member': member})


@login_required
@management_required
def staff_create(request):
    form = StaffProfileForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        member = form.save(commit=False)

        # Build a unique username: jsmith, jsmith2, jsmith3, …
        base = ((member.first_name[:1] + member.last_name).lower().replace(' ', '') or 'user')
        username = base
        counter = 2
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        member.username = username

        # Set a temporary password — user must change on first login
        temp_password = get_random_string(12)
        member.set_password(temp_password)
        member.save()

        # Create the linked StaffProfile (required for staff list / directory)
        StaffProfile.objects.get_or_create(
            user=member,
            defaults={'centre': form.cleaned_data.get('centre'), 'is_active': True},
        )

        messages.success(
            request,
            f'Staff member "{member.get_full_name()}" created. '
            f'Temporary password: {temp_password} — share this securely.',
        )
        return redirect('staff:detail', pk=member.pk)
    return render(request, 'staff/form.html', {'form': form, 'action': 'Add'})


@login_required
@management_required
def staff_edit(request, pk):
    member = get_object_or_404(User, pk=pk)
    form = StaffProfileForm(request.POST or None, instance=member)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Staff member "{member.get_full_name()}" updated.')
        return redirect('staff:detail', pk=member.pk)
    return render(request, 'staff/form.html', {'form': form, 'action': 'Edit', 'object': member})


@login_required
@management_required
def staff_delete(request, pk):
    member = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        name = member.get_full_name()
        member.is_active = False
        member.save()
        messages.success(request, f'Staff member "{name}" deactivated.')
        return redirect('staff:list')
    return render(request, 'confirm_delete.html', {
        'object': member,
        'object_name': member.get_full_name(),
        'cancel_url': 'staff:detail',
        'cancel_pk': member.pk,
    })
