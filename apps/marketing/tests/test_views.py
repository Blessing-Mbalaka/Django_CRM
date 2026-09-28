from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase

from apps.accounts.models import User


class MarketingWorkspaceViewTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="marketing-ui", role=User.Role.ADMIN)
        self.client.force_login(self.manager)

    def test_growth_is_the_complete_marketing_workspace_shell(self):
        response = self.client.get("/growth/")
        self.assertEqual(response.status_code, 200)
        for route, label in (
            ("dashboard", "Dashboard"), ("campaigns", "Campaigns"),
            ("advertising", "Advertising"), ("content", "Posters &amp; Content"),
            ("email", "Email Marketing"), ("calendar", "Marketing Calendar"),
            ("leads", "Leads"), ("analytics", "Analytics"), ("brand", "Brand Kit"),
        ):
            with self.subTest(route=route):
                self.assertContains(response, f'data-route="{route}"')
                self.assertContains(response, label)
        self.assertContains(response, "Marketing &amp; Advertising")
        self.assertContains(response, 'href="/academy/#tools"')
        self.assertContains(response, 'id="sidebar"')
        self.assertContains(response, '<dialog id="marketingDialog"')
        self.assertContains(response, 'id="marketing-config"')
        self.assertContains(response, 'id="providerStatus"')
        self.assertContains(response, 'method="post" action="/accounts/logout/"')
        self.assertContains(response, '"canManage": true')
        self.assertNotContains(response, "Coming soon")
        self.assertNotContains(response, "Sample workspace")
        self.assertNotContains(response, "Changes reset on refresh")
        self.assertNotContains(response, "../marketing-app/index.html")
        self.assertNotContains(response, 'class="navbar')

    def test_reader_shell_exposes_read_only_management_flag(self):
        reader = User.objects.create_user(username="marketing-reader", role=User.Role.STAFF)
        self.client.force_login(reader)
        response = self.client.get("/growth/")
        self.assertContains(response, '"canManage": false')

    def test_assets_are_maintained_modules_without_prototype_data(self):
        for asset in (
            "sme/marketing/css/style.css", "sme/marketing/js/api.js", "sme/marketing/js/views.js",
            "sme/marketing/js/forms.js", "sme/marketing/js/charts.js", "sme/marketing/js/app.js",
        ):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
        app = Path(finders.find("sme/marketing/js/app.js")).read_text(encoding="utf-8")
        api = Path(finders.find("sme/marketing/js/api.js")).read_text(encoding="utf-8")
        self.assertNotIn("localStorage", app + api)
        self.assertNotIn("js/data.js", app + api)
        self.assertIn("/api/v1/marketing/", api)

    def test_academy_and_suite_navigation_link_to_canonical_marketing_route(self):
        academy = self.client.get("/academy/")
        self.assertContains(academy, "/growth/")
        self.assertNotContains(academy, "../marketing-app/index.html")

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        response = self.client.get("/growth/")
        self.assertRedirects(response, "/accounts/login/?next=/growth/", fetch_redirect_response=False)
