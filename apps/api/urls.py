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
from apps.ai.api_views             import ai_insights, run_pipeline as ai_run_pipeline, training_readiness
from apps.documents.api_views      import DocumentLibraryViewSet, DocumentViewSet, DocumentVersionViewSet, FolderViewSet
from apps.tasks.api_views          import BoardColumnViewSet, BoardViewSet, TaskActivityViewSet, TaskCommentViewSet, TaskViewSet
from apps.billing.api_views        import InvoiceLineViewSet, InvoiceViewSet, PaymentViewSet
from apps.expenses.api_views       import ExpenseCategoryViewSet, ExpenseViewSet
from apps.accounting.api_views     import AccountViewSet, AccountingPeriodViewSet, JournalEntryViewSet
from apps.products.api_views       import ProductViewSet
from apps.inventory.api_views      import ReorderRuleViewSet, StockLocationViewSet, StockMovementViewSet
from apps.purchasing.api_views     import GoodsReceiptViewSet, PurchaseOrderLineViewSet, PurchaseOrderViewSet, SupplierBillViewSet, SupplierViewSet
from apps.sales.api_views          import FulfilmentViewSet, SalesOrderLineViewSet, SalesOrderViewSet

router = DefaultRouter()
router.register(r'clients',       ClientViewSet,          basename='client')
router.register(r'engagements',   EngagementViewSet,      basename='engagement')
router.register(r'centres',       CentreViewSet,          basename='centre')
router.register(r'staff',         StaffViewSet,           basename='staff')
router.register(r'finance',       FinancialRecordViewSet, basename='finance')
router.register(r'alerts',        AlertViewSet,           basename='alert')
router.register(r'communication', CommunicationLogViewSet, basename='communication')
router.register(r'users',         UserViewSet,            basename='user')
router.register(r'document-libraries', DocumentLibraryViewSet, basename='document-library')
router.register(r'document-folders', FolderViewSet, basename='document-folder')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-versions', DocumentVersionViewSet, basename='document-version')
router.register(r'task-boards', BoardViewSet, basename='task-board')
router.register(r'task-columns', BoardColumnViewSet, basename='task-column')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-comments', TaskCommentViewSet, basename='task-comment')
router.register(r'task-activity', TaskActivityViewSet, basename='task-activity')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-lines', InvoiceLineViewSet, basename='invoice-line')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'accounting-periods', AccountingPeriodViewSet, basename='accounting-period')
router.register(r'journals', JournalEntryViewSet, basename='journal')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stock-locations', StockLocationViewSet, basename='stock-location')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movement')
router.register(r'reorder-rules', ReorderRuleViewSet, basename='reorder-rule')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-lines', PurchaseOrderLineViewSet, basename='purchase-order-line')
router.register(r'goods-receipts', GoodsReceiptViewSet, basename='goods-receipt')
router.register(r'supplier-bills', SupplierBillViewSet, basename='supplier-bill')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'sales-order-lines', SalesOrderLineViewSet, basename='sales-order-line')
router.register(r'fulfilments', FulfilmentViewSet, basename='fulfilment')


@api_view(['GET'])
def api_root(request, format=None):
    """
    JBS CRM REST API v1.0 — Browsable interface.
    Authentication: Session (browser) or Token — Authorization: Token <key>
    """
    return Response({
        'status':    'JBS CRM API v1.0 — Phase 1', # Informational endpoint with API overview
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
            'ai_insights':   reverse('ai-insights',          request=request, format=format),
            'documents':     reverse('document-list',        request=request, format=format),
            'task_boards':   reverse('task-board-list',      request=request, format=format),
            'tasks':         reverse('task-list',            request=request, format=format),
            'invoices':      reverse('invoice-list',         request=request, format=format),
            'expenses':      reverse('expense-list',         request=request, format=format),
            'accounts':      reverse('account-list',         request=request, format=format),
            'journals':      reverse('journal-list',         request=request, format=format),
            'products':      reverse('product-list',         request=request, format=format),
            'stock':         reverse('stock-movement-list',  request=request, format=format),
            'purchasing':    reverse('purchase-order-list',  request=request, format=format),
            'sales_orders':  reverse('sales-order-list',     request=request, format=format),
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('analytics/', analytics_report, name='analytics-report'),
    path('ai/insights/', ai_insights, name='ai-insights'),
    path('ai/run-pipeline/', ai_run_pipeline, name='ai-run-pipeline'),
    path('ai/readiness/', training_readiness, name='ai-readiness'),
    path('', include(router.urls)),
]
