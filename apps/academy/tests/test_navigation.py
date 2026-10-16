from django.test import TestCase

from apps.accounts.models import User


class AcademyToolNavigationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="academy-tool-navigation")
        self.client.force_login(self.user)

    def test_business_tools_contains_only_six_ordered_primary_apps(self):
        response = self.client.get("/academy/")

        tools = response.context["academy_tools"]
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
        secondary_labels = {
            "Engagements", "Accounting", "Payroll Management", "System Admin",
            "Business Diagnostic", "API Explorer",
        }
        self.assertTrue(secondary_labels.isdisjoint(item["label"] for item in tools))
