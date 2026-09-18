from django.urls import reverse


# Inline paths adapted from the original SME prototype icon set. Keeping the
# geometry in the server-owned registry makes every launcher independent of an
# icon CDN and lets Academy reuse the exact same icon and URL contract.
SME_ICON_PATHS = {
    'bi-people': 'M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 21v-4a6 4 0 0 1 12 0v4M17 11a3 3 0 1 0 0-6M15 21v-4a6 4 0 0 1 7-4',
    'bi-briefcase': 'M4 7h16v13H4zM9 7V4h6v3M4 12h16M10 12v2h4v-2',
    'bi-bag-check': 'M5 8h14l-1 13H6zM9 8V6a3 3 0 0 1 6 0v2M9 14l2 2 4-4',
    'bi-receipt': 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h4',
    'bi-wallet2': 'M3 6h16v14H3zM3 9h18v8h-5a4 4 0 0 1 0-8h5M16 12h.01',
    'bi-cash-coin': 'M3 6h14v10H3zM6 9a2 2 0 0 1-2 2M14 9a2 2 0 0 0 2 2M10 9v4M19 12a3 3 0 1 1 0 6',
    'bi-journal-text': 'M5 3h14v18H5zM8 3v18M11 8h5M11 12h5M11 16h3',
    'bi-activity': 'M3 12h4l2-7 4 14 2-7h6',
    'bi-people-fill': 'M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 21v-4a6 4 0 0 1 12 0v4M17 6h5v8h-3l-2 3z',
    'bi-box-seam': 'm3 7 9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10',
    'bi-boxes': 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    'bi-cart-check': 'M3 4h2l2 11h10l3-7H6M9 19h.01M17 19h.01M10 11l2 2 4-4',
    'bi-kanban': 'M4 4h5v16H4zM11 4h5v10h-5zM18 4h3v7h-3z',
    'bi-folder2-open': 'M3 6h7l2 2h9l-2 11H4zM3 6v13',
    'bi-bar-chart-line': 'M4 20V10M10 20V4M16 20v-7M22 20H2M3 8l6-5 6 7 6-5',
    'bi-bell': 'M6 17h12l-2-3V9a4 4 0 0 0-8 0v5zM10 20h4',
    'bi-chat-dots': 'M3 4h18v13H9l-5 4v-4H3zM7 10h.01M12 10h.01M17 10h.01',
    'bi-cpu': 'M8 8h8v8H8zM9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M20 9h3M1 15h3M20 15h3',
    'bi-person-badge': 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21v-3a8 5 0 0 1 16 0v3M17 3h5v6h-5z',
    'bi-building': 'M4 21V3h11v18M15 9h5v12M8 7h3M8 11h3M8 15h3M18 13h.01M18 17h.01',
    'bi-shield-check': 'M12 3l8 3v6c0 5-3 8-8 10-5-2-8-5-8-10V6zM8 12l3 3 5-6',
    'bi-mortarboard': 'M2 9l10-5 10 5-10 5zM6 11v5c3 3 9 3 12 0v-5M22 9v7',
    'bi-clipboard-data': 'M7 4h10v17H5V6h4M9 3h6v4H9zM9 17v-4M13 17V9M17 17v-6',
    'bi-megaphone': 'M3 10v4h4l9 4V6l-9 4zM7 14l2 6h3l-2-5M19 9l3-2M19 15l3 2',
    'bi-share': 'M18 5a3 3 0 1 0 0 .01M6 12a3 3 0 1 0 0 .01M18 19a3 3 0 1 0 0 .01M9 11l6-4M9 13l6 4',
    'bi-funnel': 'M3 4h18l-7 8v7l-4 2v-9z',
    'bi-globe2': 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18',
    'bi-bezier2': 'M5 4h4v4H5zM15 16h4v4h-4zM9 6h6a4 4 0 0 1 4 4v6M7 8v6a4 4 0 0 0 4 4h4',
    'bi-rocket-takeoff': 'M7 15l-3 1 4-7 7-5 5 0 0 5-5 7-7 4 1-3M13 11l-2 2M6 18l-2 3 3-1',
    'bi-braces': 'M8 3H6a2 2 0 0 0-2 2v4a2 2 0 0 1-2 2 2 2 0 0 1 2 2v4a2 2 0 0 0 2 2h2M16 3h2a2 2 0 0 1 2 2v4a2 2 0 0 0 2 2 2 2 0 0 0-2 2v4a2 2 0 0 1-2 2h-2',
}
DEFAULT_SME_ICON = 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z'


MODULE_HELP = {
    'CRM & Customers': 'A CRM is one shared place for customer details, ownership and relationship history.',
    'Engagements': 'An engagement is a piece of work or a business opportunity linked to a customer.',
    'Sales Orders': 'A sales order records what a customer has agreed to buy, including price and quantity.',
    'Invoicing & Billing': 'An invoice is a formal request asking a customer to pay for goods or services.',
    'Expense Tracking': 'An expense is money the organisation spends to operate or deliver work.',
    'Financial Overview': 'A financial overview is a simple summary of revenue, costs, profit, cash and pipeline.',
    'Accounting': 'Accounting records every financial event in a balanced and traceable ledger.',
    'Business Activity': 'Business activity combines money, purchasing and stock movements on one timeline.',
    'Payroll Management': 'Payroll calculates and records employee pay, deductions and payment totals.',
    'Products & Services': 'A product or service is something the organisation buys, sells or delivers.',
    'Inventory': 'Inventory is the quantity and value of physical stock currently available.',
    'Purchasing': 'Purchasing manages what the organisation orders from suppliers and what it owes them.',
    'Tasks & Kanban': 'A Kanban board shows work as cards moving through stages from start to completion.',
    'Documents': 'Documents are controlled files stored with owners, folders and version history.',
    'Reports & Analytics': 'Reports turn business records into totals, trends and information for decisions.',
    'Alerts': 'An alert highlights something risky, overdue or needing attention.',
    'Comms Health': 'Communication health shows whether customer relationships are receiving regular contact.',
    'AI Insights': 'AI insights use existing business data to highlight patterns and possible next actions.',
    'Staff': 'Staff records describe the people who work in the organisation and their responsibilities.',
    'Departments': 'A department groups related staff, customers and work under one business area.',
    'System Admin': 'System administration controls users, access and important application settings.',
    'Campaigns': 'A campaign is a planned set of messages or activities aimed at a business goal.',
    'Audience Segments': 'An audience segment is a group of people or customers with something in common.',
    'Lead Generation': 'Lead generation is the process of finding people who may become customers.',
    'Channel Performance': 'Channel performance shows which marketing channels produce useful results.',
    'Marketing Automation': 'Marketing automation schedules repeatable messages and follow-up steps.',
    'Growth & Marketing': 'Growth and marketing helps attract, understand and retain customers.',
    'SME Academy': 'The SME Academy provides administrator-managed practical courses for business owners and teams.',
    'API Explorer': 'An API explorer lets developers inspect and test the data endpoints used by the app.',
}


def _item(label, icon, url_name, description):
    return {
        'label': label,
        'icon': icon,
        'url': reverse(url_name),
        'description': description,
        'help_text': MODULE_HELP.get(label, description),
        'svg_path': SME_ICON_PATHS.get(icon, DEFAULT_SME_ICON),
    }


def _direct_item(label, icon, url, description, **extra):
    return {
        'label': label,
        'icon': icon,
        'svg_path': SME_ICON_PATHS.get(icon, DEFAULT_SME_ICON),
        'url': url,
        'description': description,
        'help_text': MODULE_HELP.get(label, description),
        **extra,
    }


def get_suite_navigation(user):
    """Canonical, role-aware module map for the dashboard catalogue."""
    groups = [
        {
            'key': 'sales', 'label': 'CRM & Customers', 'icon': 'bi-people', 'gradient': 'crm',
            'description': 'Manage customer relationships from first contact through engagement and confirmed sales.',
            'items': [
                _item('CRM & Customers', 'bi-people', 'clients:list', 'Keep customer profiles, ownership and relationship information together.'),
                _item('Engagements', 'bi-briefcase', 'engagements:list', 'Track opportunities, active work, owners and engagement progress.'),
                _item('Sales Orders', 'bi-bag-check', 'sales:orders', 'Create, confirm, fulfil and invoice customer orders.'),
            ],
        },
        {
            'key': 'finance', 'label': 'Finance & Accounting', 'icon': 'bi-cash-stack', 'gradient': 'finance',
            'description': 'Control billing, costs, cash, payroll and the canonical accounting ledger.',
            'items': [
                _item('Invoicing & Billing', 'bi-receipt', 'billing:invoices', 'Issue customer invoices and record payments against outstanding balances.'),
                _item('Expense Tracking', 'bi-wallet2', 'expenses:expenses', 'Submit, approve and pay business expenses with a complete audit trail.'),
                _item('Financial Overview', 'bi-cash-coin', 'finance:overview', 'Review ledger-backed revenue, expenses, profit and forecast pipeline.'),
                _item('Accounting', 'bi-journal-text', 'accounting:ledger', 'Work with journals, statements and bank reconciliation.'),
                _item('Business Activity', 'bi-activity', 'analytics:reports', 'Compare financial, purchasing and inventory activity in one filtered chart.'),
            ],
        },
        {
            'key': 'operations', 'label': 'Operations', 'icon': 'bi-box-seam', 'gradient': 'operations',
            'description': 'Run products, purchasing, stock, tasks and the documents supporting daily delivery.',
            'items': [
                _item('Products & Services', 'bi-box-seam', 'products:catalogue', 'Maintain the shared catalogue, prices, costs, tax rates and item types.'),
                _item('Inventory', 'bi-boxes', 'inventory:inventory', 'Monitor stock locations, movements, availability and reorder levels.'),
                _item('Purchasing', 'bi-cart-check', 'purchasing:orders', 'Manage suppliers, purchase orders, receipts, bills and supplier payments.'),
                _item('Tasks & Kanban', 'bi-kanban', 'tasks:board', 'Plan and move operational work through collaborative boards.'),
                _item('Documents', 'bi-folder2-open', 'documents:library', 'Store controlled documents, folders and file versions.'),
            ],
        },
        {
            'key': 'insights', 'label': 'Insights & Control', 'icon': 'bi-graph-up-arrow', 'gradient': 'insights',
            'description': 'Turn operational data into reports, alerts, communication health and assisted insights.',
            'items': [
                _item('Reports & Analytics', 'bi-bar-chart-line', 'analytics:reports', 'Explore performance, pipeline, engagement health and business activity.'),
                _item('Alerts', 'bi-bell', 'alerts:list', 'Review unresolved risks, overdue payments and operational warnings.'),
                _item('Comms Health', 'bi-chat-dots', 'communication:health', 'Monitor relationship contact history and communication coverage.'),
                _item('AI Insights', 'bi-cpu', 'ai:insights', 'Use rule-based intelligence, forecasts and readiness indicators.'),
            ],
        },
        {
            'key': 'people', 'label': 'People & Administration', 'icon': 'bi-person-gear', 'gradient': 'people',
            'description': 'Manage staff, departments and permitted system administration functions.',
            'items': [
                _item('Staff', 'bi-person-badge', 'staff:list', 'Maintain staff profiles, roles, departments and availability.'),
                _item('Departments', 'bi-building', 'centres:list', 'Organise clients, engagements and staff by business department.'),
            ],
        },
        {
            'key': 'growth', 'label': 'Growth & Marketing', 'icon': 'bi-megaphone', 'gradient': 'growth',
            'description': 'Prepare future campaigns, audience segments, lead generation and channel performance.',
            'items': [
                _item('SME Academy', 'bi-mortarboard', 'academy:index', 'Learn through practical courses managed by Academy administrators.'),
                _item('Growth & Marketing', 'bi-rocket-takeoff', 'core:growth_marketing', 'Preview the planned growth and marketing workspace.'),
            ],
            'catalogue_items': [
                _item('SME Academy', 'bi-mortarboard', 'academy:index', 'Learn through practical courses managed by Academy administrators.'),
                _direct_item('Business Diagnostic', 'bi-clipboard-data', f"{reverse('academy:index')}#diagnostics", 'Assess your business using administrator-configured questions, scoring and course recommendations.'),
                {**_item('Campaigns', 'bi-megaphone', 'core:growth_marketing', 'Plan coordinated email, event and relationship campaigns.'), 'coming_soon': True},
                {**_item('Audience Segments', 'bi-share', 'core:growth_marketing', 'Build focused audiences from CRM and engagement information.'), 'coming_soon': True},
                {**_item('Lead Generation', 'bi-funnel', 'core:growth_marketing', 'Capture acquisition sources and qualify interest into engagements.'), 'coming_soon': True},
                {**_item('Channel Performance', 'bi-globe2', 'core:growth_marketing', 'Compare reach, conversion and contribution across channels.'), 'coming_soon': True},
                {**_item('Marketing Automation', 'bi-bezier2', 'core:growth_marketing', 'Prepare repeatable journeys while preserving human oversight.'), 'coming_soon': True},
            ],
        },
    ]

    role = getattr(user, 'role', None)
    if user.is_superuser or role in ('dean', 'admin'):
        groups[1]['items'].insert(4, _item('Payroll Management', 'bi-people-fill', 'payroll:payroll', 'Prepare, approve and pay controlled payroll runs.'))
    if user.is_superuser or user.is_staff or role in ('dean', 'admin'):
        groups[4]['items'].append(_item('System Admin', 'bi-shield-check', 'admin_panel:dashboard', 'Manage system users, access and administrative controls.'))
    catalogue_order = {'finance': 0, 'operations': 1, 'sales': 2, 'growth': 3, 'insights': 4, 'people': 5}
    groups.sort(key=lambda group: catalogue_order[group['key']])
    groups.append({
        'key': 'developer', 'label': 'Developer', 'icon': 'bi-code-slash', 'gradient': 'developer',
        'description': 'Inspect and test the suite’s authenticated REST API endpoints.',
        'items': [_direct_item('API Explorer', 'bi-braces', '/api/v1/', 'Open the browsable REST API.', external=True)],
    })
    for group in groups:
        group['svg_path'] = SME_ICON_PATHS.get(group['icon'], DEFAULT_SME_ICON)
        group.setdefault('catalogue_items', group['items'])
    return groups
