from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from functionalities.analytics import services


@login_required
def reports_view(request):
    context = services.get_reports_context()
    return render(request, 'analytics/reports.html', context)
