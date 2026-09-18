"""
JBS CRM — Root URL Configuration
All app URLs are included here for clean modular routing.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django built-in admin
    path('admin/', admin.site.urls),

    # Authentication (login, logout, password reset)
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Dashboard / home
    path('', include('apps.core.urls', namespace='core')),

    # Domain apps
    path('staff/', include('apps.staff.urls', namespace='staff')),
    path('departments/', include('apps.centres.urls', namespace='centres')),
    path('centres/', include('apps.centres.urls', namespace='centres_legacy')),
    path('clients/', include('apps.clients.urls', namespace='clients')),
    path('engagements/', include('apps.engagements.urls', namespace='engagements')),
    path('finance/', include('apps.finance.urls', namespace='finance')),
    path('alerts/', include('apps.alerts.urls', namespace='alerts')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('communication/', include('apps.communication.urls', namespace='communication')),
    path('system-admin/', include('apps.admin_panel.urls', namespace='admin_panel')),
    path('ai/', include('apps.ai.urls', namespace='ai')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('expenses/', include('apps.expenses.urls', namespace='expenses')),
    path('products/', include('apps.products.urls', namespace='products')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('purchasing/', include('apps.purchasing.urls', namespace='purchasing')),
    path('sales/', include('apps.sales.urls', namespace='sales')),
    path('accounting/', include('apps.accounting.urls', namespace='accounting')),
    path('payroll/', include('apps.payroll.urls', namespace='payroll')),
    path('academy/', include('apps.academy.urls', namespace='academy')),

    # Versioned REST API; legacy /api/ routes remain for current clients.
    path('api/v1/', include('apps.api.urls')),

    # REST Framework browsable API + token auth
    path('api/', include('apps.api.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
