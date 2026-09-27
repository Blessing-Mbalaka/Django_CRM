from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard_view(request):
    """
    Send authenticated users to the canonical Academy workspace.
    """
    return redirect('academy:index')


@login_required
def growth_marketing_view(request):
    return render(request, 'core/growth_marketing.html')

