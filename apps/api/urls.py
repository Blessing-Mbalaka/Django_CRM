"""
JBS CRM — REST API Router
All API endpoints registered here for a unified browsable API at /api/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.clients.api_views       import ClientViewSet
from apps.engagements.api_views    import EngagementViewSet
from apps.centres.api_views        import CentreViewSet
from apps.staff.api_views          import StaffViewSet
from apps.finance.api_views        import FinancialRecordViewSet
from apps.alerts.api_views         import AlertViewSet
from apps.communication.api_views  import CommunicationLogViewSet
from apps.accounts.api_views       import UserViewSet
from apps.analytics.api_views      import analytics_report

router = DefaultRouter()
router.register(r'clients',       ClientViewSet,          basename='client')
router.register(r'engagements',   EngagementViewSet,      basename='engagement')
router.register(r'centres',       CentreViewSet,          basename='centre')
router.register(r'staff',         StaffViewSet,           basename='staff')
router.register(r'finance',       FinancialRecordViewSet, basename='finance')
router.register(r'alerts',        AlertViewSet,           basename='alert')
router.register(r'communication', CommunicationLogViewSet, basename='communication')
router.register(r'users',         UserViewSet,            basename='user')


@api_view(['GET'])
def api_root(request, format=None):
    """
    JBS CRM REST API v1.0 — Browsable interface.
    Authentication: Session (browser) or Token — Authorization: Token <key>
    """
    return Response({
        'status':    'JBS CRM API v1.0 — Phase 1',
        'database':  'SQLite (Phase 1)',
        'framework': 'Django REST Framework',
        'endpoints': {
            'clients':       reverse('client-list',        request=request, format=format),
            'engagements':   reverse('engagement-list',    request=request, format=format),
            'centres':       reverse('centre-list',        request=request, format=format),
            'staff':         reverse('staff-list',         request=request, format=format),
            'finance':       reverse('finance-list',       request=request, format=format),
            'alerts':        reverse('alert-list',         request=request, format=format),
            'communication': reverse('communication-list', request=request, format=format),
            'users':         reverse('user-list',          request=request, format=format),
            'analytics':     reverse('analytics-report',   request=request, format=format),
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('analytics/', analytics_report, name='analytics-report'),
    path('', include(router.urls)),
]
