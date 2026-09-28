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
from apps.analytics.api_views      import analytics_report, business_activity
from apps.ai.api_views             import ai_insights, run_pipeline as ai_run_pipeline, training_readiness
from apps.documents.api_views      import DocumentLibraryViewSet, DocumentViewSet, DocumentVersionViewSet, FolderViewSet
from apps.tasks.api_views          import BoardColumnViewSet, BoardViewSet, ProjectViewSet, TaskActivityViewSet, TaskAttachmentViewSet, TaskCommentViewSet, TaskViewSet
from apps.billing.api_views        import InvoiceLineViewSet, InvoiceViewSet, PaymentViewSet
from apps.expenses.api_views       import ExpenseCategoryViewSet, ExpenseViewSet
from apps.accounting.api_views     import AccountViewSet, AccountingPeriodViewSet, BankStatementLineViewSet, BankStatementViewSet, JournalEntryViewSet, balance_sheet_report, income_statement_report, trial_balance_report
from apps.products.api_views       import ProductViewSet
from apps.inventory.api_views      import InventoryCategoryViewSet, InventoryProductViewSet, InventorySettingsViewSet, InventoryWorkspaceViewSet, ReorderRuleViewSet, StockLocationViewSet, StockMovementViewSet
from apps.purchasing.api_views     import GoodsReceiptViewSet, PurchaseOrderLineViewSet, PurchaseOrderViewSet, SupplierBillViewSet, SupplierViewSet
from apps.sales.api_views          import FulfilmentViewSet, SalesOrderLineViewSet, SalesOrderViewSet
from apps.payroll.api_views        import PayrollEmployeeViewSet, PayRunViewSet, PayslipViewSet
from apps.marketing.api_views import (
    BrandKitViewSet, MarketingActivityViewSet, MarketingAdvertViewSet,
    MarketingCampaignViewSet, MarketingContactViewSet, MarketingContentViewSet,
    MarketingLeadViewSet, MarketingMetricViewSet, MarketingWorkspaceViewSet,
    OutboundMessageViewSet,
)
from apps.academy.api_views import (
    AcademyEventViewSet, AcademyResourceViewSet, ChatMessageViewSet,
    ConversationViewSet, CourseCategoryViewSet, CourseEnrollmentViewSet,
    CourseLevelViewSet, CourseViewSet, DiagnosticCategoryViewSet,
    DiagnosticViewSet, EventCategoryViewSet, ForumCategoryViewSet,
    ForumPostViewSet, ForumReplyViewSet, FundingOpportunityViewSet,
    LearningPathViewSet, MentorProfileViewSet, MentorshipBookingViewSet,
    OpportunityCategoryViewSet, ResourceCategoryViewSet,
)
from apps.academy.management_views import (
    AcademyEventManagementViewSet, AcademyResourceManagementViewSet,
    CourseCategoryManagementViewSet, CourseLevelManagementViewSet,
    CourseManagementViewSet, CourseModuleManagementViewSet,
    DiagnosticCategoryManagementViewSet, DiagnosticManagementViewSet,
    DiagnosticOptionManagementViewSet, DiagnosticQuestionManagementViewSet,
    DiagnosticRecommendationManagementViewSet, EventCategoryManagementViewSet,
    ForumCategoryManagementViewSet, ForumPostManagementViewSet,
    FundingOpportunityManagementViewSet, LearningPathManagementViewSet,
    MentorProfileManagementViewSet, OpportunityCategoryManagementViewSet,
    ResourceCategoryManagementViewSet,
)

router = DefaultRouter()
router.register(r'clients',       ClientViewSet,          basename='client')
router.register(r'engagements',   EngagementViewSet,      basename='engagement')
router.register(r'departments',   CentreViewSet,          basename='department')
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
router.register(r'task-attachments', TaskAttachmentViewSet, basename='task-attachment')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-lines', InvoiceLineViewSet, basename='invoice-line')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'accounting-periods', AccountingPeriodViewSet, basename='accounting-period')
router.register(r'journals', JournalEntryViewSet, basename='journal')
router.register(r'bank-statements', BankStatementViewSet, basename='bank-statement')
router.register(r'bank-statement-lines', BankStatementLineViewSet, basename='bank-statement-line')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stock-locations', StockLocationViewSet, basename='stock-location')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movement')
router.register(r'reorder-rules', ReorderRuleViewSet, basename='reorder-rule')
router.register(r'inventory-categories', InventoryCategoryViewSet, basename='inventory-category')
router.register(r'inventory-products', InventoryProductViewSet, basename='inventory-product')
router.register(r'inventory-settings', InventorySettingsViewSet, basename='inventory-settings')
router.register(r'inventory', InventoryWorkspaceViewSet, basename='inventory-workspace')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-lines', PurchaseOrderLineViewSet, basename='purchase-order-line')
router.register(r'goods-receipts', GoodsReceiptViewSet, basename='goods-receipt')
router.register(r'supplier-bills', SupplierBillViewSet, basename='supplier-bill')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'sales-order-lines', SalesOrderLineViewSet, basename='sales-order-line')
router.register(r'fulfilments', FulfilmentViewSet, basename='fulfilment')
router.register(r'payroll-employees', PayrollEmployeeViewSet, basename='payroll-employee')
router.register(r'pay-runs', PayRunViewSet, basename='pay-run')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'academy/paths', LearningPathViewSet, basename='academy-path')
router.register(r'academy/courses', CourseViewSet, basename='academy-course')
router.register(r'academy/course-categories', CourseCategoryViewSet, basename='academy-course-category')
router.register(r'academy/course-levels', CourseLevelViewSet, basename='academy-course-level')
router.register(r'academy/enrollments', CourseEnrollmentViewSet, basename='academy-enrollment')
router.register(r'academy/resources', AcademyResourceViewSet, basename='academy-resource')
router.register(r'academy/resource-categories', ResourceCategoryViewSet, basename='academy-resource-category')
router.register(r'academy/diagnostics', DiagnosticViewSet, basename='academy-diagnostic')
router.register(r'academy/diagnostic-categories', DiagnosticCategoryViewSet, basename='academy-diagnostic-category')
router.register(r'academy/funding', FundingOpportunityViewSet, basename='academy-funding')
router.register(r'academy/opportunity-categories', OpportunityCategoryViewSet, basename='academy-opportunity-category')
router.register(r'academy/events', AcademyEventViewSet, basename='academy-event')
router.register(r'academy/event-categories', EventCategoryViewSet, basename='academy-event-category')
router.register(r'academy/mentors', MentorProfileViewSet, basename='academy-mentor')
router.register(r'academy/mentorship-bookings', MentorshipBookingViewSet, basename='academy-mentorship-booking')
router.register(r'academy/conversations', ConversationViewSet, basename='academy-conversation')
router.register(r'academy/messages', ChatMessageViewSet, basename='academy-message')
router.register(r'academy/forum/categories', ForumCategoryViewSet, basename='academy-forum-category')
router.register(r'academy/forum/posts', ForumPostViewSet, basename='academy-forum-post')
router.register(r'academy/forum/replies', ForumReplyViewSet, basename='academy-forum-reply')
router.register(r'academy/manage/course-categories', CourseCategoryManagementViewSet, basename='academy-manage-course-category')
router.register(r'academy/manage/course-levels', CourseLevelManagementViewSet, basename='academy-manage-course-level')
router.register(r'academy/manage/paths', LearningPathManagementViewSet, basename='academy-manage-path')
router.register(r'academy/manage/courses', CourseManagementViewSet, basename='academy-manage-course')
router.register(r'academy/manage/modules', CourseModuleManagementViewSet, basename='academy-manage-module')
router.register(r'academy/manage/resource-categories', ResourceCategoryManagementViewSet, basename='academy-manage-resource-category')
router.register(r'academy/manage/resources', AcademyResourceManagementViewSet, basename='academy-manage-resource')
router.register(r'academy/manage/diagnostic-categories', DiagnosticCategoryManagementViewSet, basename='academy-manage-diagnostic-category')
router.register(r'academy/manage/diagnostics', DiagnosticManagementViewSet, basename='academy-manage-diagnostic')
router.register(r'academy/manage/diagnostic-questions', DiagnosticQuestionManagementViewSet, basename='academy-manage-diagnostic-question')
router.register(r'academy/manage/diagnostic-options', DiagnosticOptionManagementViewSet, basename='academy-manage-diagnostic-option')
router.register(r'academy/manage/diagnostic-recommendations', DiagnosticRecommendationManagementViewSet, basename='academy-manage-diagnostic-recommendation')
router.register(r'academy/manage/opportunity-categories', OpportunityCategoryManagementViewSet, basename='academy-manage-opportunity-category')
router.register(r'academy/manage/funding', FundingOpportunityManagementViewSet, basename='academy-manage-funding')
router.register(r'academy/manage/event-categories', EventCategoryManagementViewSet, basename='academy-manage-event-category')
router.register(r'academy/manage/events', AcademyEventManagementViewSet, basename='academy-manage-event')
router.register(r'academy/manage/mentors', MentorProfileManagementViewSet, basename='academy-manage-mentor')
router.register(r'academy/manage/forum-categories', ForumCategoryManagementViewSet, basename='academy-manage-forum-category')
router.register(r'academy/manage/forum-posts', ForumPostManagementViewSet, basename='academy-manage-forum-post')
router.register(r'marketing/campaigns', MarketingCampaignViewSet, basename='marketing-campaign')
router.register(r'marketing/adverts', MarketingAdvertViewSet, basename='marketing-advert')
router.register(r'marketing/content', MarketingContentViewSet, basename='marketing-content')
router.register(r'marketing/contacts', MarketingContactViewSet, basename='marketing-contact')
router.register(r'marketing/leads', MarketingLeadViewSet, basename='marketing-lead')
router.register(r'marketing/activities', MarketingActivityViewSet, basename='marketing-activity')
router.register(r'marketing/metrics', MarketingMetricViewSet, basename='marketing-metric')
router.register(r'marketing/brand-kit', BrandKitViewSet, basename='marketing-brand-kit')
router.register(r'marketing/outbound-messages', OutboundMessageViewSet, basename='marketing-outbound-message')
router.register(r'marketing/workspace', MarketingWorkspaceViewSet, basename='marketing-workspace')


@api_view(['GET'])
def api_root(request, format=None):
    """
    JBS CRM REST API v1.0 — Browsable interface.
    Authentication: Session (browser) or Token — Authorization: Token <key>
    """
    return Response({
        'status':    'JBS SME Suite API v1.0 — Release candidate',
        'database':  'SQLite (development)',
        'framework': 'Django REST Framework',
        'endpoints': {
            'clients':       reverse('client-list',        request=request, format=format),
            'engagements':   reverse('engagement-list',    request=request, format=format),
            'departments':   reverse('department-list',    request=request, format=format),
            'centres_legacy': reverse('centre-list',       request=request, format=format),
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
            'bank_statements': reverse('bank-statement-list', request=request, format=format),
            'trial_balance': reverse('trial-balance-report',  request=request, format=format),
            'products':      reverse('product-list',         request=request, format=format),
            'stock':         reverse('stock-movement-list',  request=request, format=format),
            'purchasing':    reverse('purchase-order-list',  request=request, format=format),
            'sales_orders':  reverse('sales-order-list',     request=request, format=format),
            'payroll':       reverse('pay-run-list',         request=request, format=format),
            'academy_paths': request.build_absolute_uri('/api/v1/academy/paths/'),
            'academy_courses': request.build_absolute_uri('/api/v1/academy/courses/'),
            'academy_resources': request.build_absolute_uri('/api/v1/academy/resources/'),
            'academy_diagnostics': request.build_absolute_uri('/api/v1/academy/diagnostics/'),
            'academy_funding': request.build_absolute_uri('/api/v1/academy/funding/'),
            'academy_events': request.build_absolute_uri('/api/v1/academy/events/'),
            'academy_mentors': request.build_absolute_uri('/api/v1/academy/mentors/'),
            'academy_forum': request.build_absolute_uri('/api/v1/academy/forum/posts/'),
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('accounting/reports/trial-balance/', trial_balance_report, name='trial-balance-report'),
    path('accounting/reports/income-statement/', income_statement_report, name='income-statement-report'),
    path('accounting/reports/balance-sheet/', balance_sheet_report, name='balance-sheet-report'),
    path('analytics/', analytics_report, name='analytics-report'),
    path('analytics/business-activity/', business_activity, name='business-activity'),
    path('ai/insights/', ai_insights, name='ai-insights'),
    path('ai/run-pipeline/', ai_run_pipeline, name='ai-run-pipeline'),
    path('ai/readiness/', training_readiness, name='ai-readiness'),
    path('', include(router.urls)),
]
