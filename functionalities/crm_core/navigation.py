from django.urls import reverse


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
        'items': [{'label': 'API Explorer', 'icon': 'bi-braces', 'url': '/api/v1/', 'description': 'Open the browsable REST API.', 'help_text': MODULE_HELP['API Explorer'], 'external': True}],
    })
    for group in groups:
        group.setdefault('catalogue_items', group['items'])
    return groups
