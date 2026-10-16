from django.test import TestCase

from apps.accounts.models import User
from functionalities.crm_core import navigation


class NavigationRegistryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="navigation-staff", role=User.Role.STAFF)

    def test_primary_tools_have_exact_order_labels_and_routes(self):
        build_tools = getattr(navigation, "get_academy_primary_tools", lambda user: [])

        tools = build_tools(self.user)

        self.assertEqual(
            [(item["label"], item["url"]) for item in tools],
            [
                ("Invoicing", "/billing/"),
                ("Inventory", "/inventory/"),
                ("Project Management", "/tasks/"),
                ("Marketing", "/growth/"),
                ("CRM", "/clients/"),
                ("Documents", "/documents/"),
            ],
        )
        self.assertTrue(all(item["description"] and item["svg_path"] for item in tools))

    def test_crm_navigation_groups_every_secondary_tool(self):
        build_navigation = getattr(navigation, "get_crm_navigation", lambda user: [])

        groups = build_navigation(self.user)

        self.assertEqual(
            [(group["label"], [item["label"] for item in group["items"]]) for group in groups],
            [
                ("Customers & Revenue", ["Customers", "Engagements", "Sales Orders"]),
                ("Finance", ["Expense Tracking", "Financial Overview", "Accounting", "Business Activity"]),
                ("Operations", ["Products & Services", "Purchasing"]),
                ("Insights", ["Reports & Analytics", "Alerts", "Communication Health", "AI Insights"]),
                ("People & Administration", ["Staff", "Departments"]),
                ("Learning & Developer", ["SME Academy", "Business Diagnostic", "API Explorer"]),
            ],
        )
        analytics_items = [
            item for group in groups for item in group["items"]
            if item["label"] in {"Business Activity", "Reports & Analytics"}
        ]
        self.assertEqual([item["url"] for item in analytics_items], ["/analytics/", "/analytics/"])

    def test_unknown_role_does_not_receive_privileged_tools(self):
        self.user.role = ""
        self.user.save(update_fields=["role"])
        build_navigation = getattr(navigation, "get_crm_navigation", lambda user: [])

        labels = [item["label"] for group in build_navigation(self.user) for item in group["items"]]

        self.assertIn("Customers", labels)
        self.assertNotIn("Payroll Management", labels)
        self.assertNotIn("System Admin", labels)

    def test_administrator_receives_payroll_and_system_admin(self):
        admin = User.objects.create_user(username="navigation-admin", role=User.Role.ADMIN)
        build_navigation = getattr(navigation, "get_crm_navigation", lambda user: [])

        labels = [item["label"] for group in build_navigation(admin) for item in group["items"]]

        self.assertIn("Payroll Management", labels)
        self.assertIn("System Admin", labels)
