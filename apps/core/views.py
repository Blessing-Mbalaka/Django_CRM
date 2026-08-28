from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    """
    Main institutional dashboard.
    Aggregates KPIs from all domain apps.
    Business logic lives in functionalities/ — views are thin.
    """
    from functionalities.crm_core.services import get_dashboard_context
    context = get_dashboard_context(request.user)
    return render(request, 'core/dashboard.html', context)


@login_required
def growth_marketing_view(request):
    return render(request, 'core/growth_marketing.html')

