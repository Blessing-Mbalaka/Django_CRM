from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator

from apps.core.decorators import exec_required
from apps.accounts.models import User


@login_required
@exec_required
def admin_dashboard(request):
    search = request.GET.get('q')
    role = request.GET.get('role')
    qs = User.objects.order_by('role', 'last_name')
    if search:
        qs = qs.filter(first_name__icontains=search) | qs.filter(last_name__icontains=search) | qs.filter(email__icontains=search)
    if role:
        qs = qs.filter(role=role)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/dashboard.html', {
        'users':       page_obj,
        'page_obj':    page_obj,
        'search':      search or '',
        'role_filter': role or '',
        'role_choices': User.Role.choices,
    })


@login_required
@exec_required
def toggle_user_active(request, pk):
    """POST-only: toggle is_active for any user (cannot deactivate yourself)."""
    if request.method != 'POST':
        return redirect('admin_panel:dashboard')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_panel:dashboard')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'{user.get_full_name()} has been {status}.')
    return redirect('admin_panel:dashboard')
