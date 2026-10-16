from functionalities.crm_core.navigation import get_crm_navigation, get_suite_navigation


CRM_SHELL_NAMESPACES = frozenset({
    'clients', 'engagements', 'sales', 'expenses', 'finance', 'accounting',
    'analytics', 'products', 'purchasing', 'alerts', 'communication', 'ai',
    'staff', 'centres', 'centres_legacy', 'payroll', 'admin_panel',
})

ACTIVE_CRM_LABELS = {
    'clients': 'Customers',
    'engagements': 'Engagements',
    'sales': 'Sales Orders',
    'expenses': 'Expense Tracking',
    'finance': 'Financial Overview',
    'accounting': 'Accounting',
    'analytics': 'Reports & Analytics',
    'products': 'Products & Services',
    'purchasing': 'Purchasing',
    'alerts': 'Alerts',
    'communication': 'Communication Health',
    'ai': 'AI Insights',
    'staff': 'Staff',
    'centres': 'Departments',
    'centres_legacy': 'Departments',
    'payroll': 'Payroll Management',
    'admin_panel': 'System Admin',
}


def suite_navigation(request):
    if not request.user.is_authenticated:
        return {
            'suite_navigation': [], 'crm_navigation': [], 'use_crm_shell': False,
            'active_crm_namespace': '', 'project_notifications': [],
            'project_notification_count': 0,
        }

    from apps.tasks.models import ProjectNotification
    namespace = getattr(request.resolver_match, 'namespace', '') or ''
    use_crm_shell = namespace in CRM_SHELL_NAMESPACES
    crm_navigation = []
    if use_crm_shell:
        active_label = ACTIVE_CRM_LABELS.get(namespace)
        crm_navigation = [
            {
                **group,
                'items': [
                    {**item, 'is_active': item['label'] == active_label}
                    for item in group['items']
                ],
            }
            for group in get_crm_navigation(request.user)
        ]
    notifications = ProjectNotification.objects.filter(recipient=request.user).select_related('project')[:8]
    return {
        'suite_navigation': get_suite_navigation(request.user),
        'crm_navigation': crm_navigation,
        'use_crm_shell': use_crm_shell,
        'active_crm_namespace': namespace if use_crm_shell else '',
        'project_notifications': notifications,
        'project_notification_count': ProjectNotification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count(),
    }
