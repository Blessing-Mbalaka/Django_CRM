from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase

from apps.accounts.models import User


class CEOApplicationSmokeTests(TestCase):
    def test_ceo_can_render_the_application_modules(self):
        ceo = User.objects.create_user(username='ceo-smoke', password='test-pass-123', role=User.Role.CEO)
        self.client.force_login(ceo)
        for path in [
            '/', '/staff/', '/departments/', '/clients/', '/engagements/', '/finance/',
            '/alerts/', '/analytics/', '/communication/', '/documents/', '/tasks/',
            '/billing/', '/expenses/', '/products/', '/inventory/', '/purchasing/',
            '/sales/', '/accounting/',
            '/payroll/',
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'id="sidebar"')
                if path == '/':
                    self.assertNotContains(response, 'Back to dashboard')
                    self.assertContains(response, 'CEO (Executive)')
                    self.assertContains(response, '/departments/')
                    self.assertContains(response, 'module-catalogue-grid')
                    self.assertContains(response, 'Finance &amp; Accounting')
                    self.assertContains(response, 'Operations')
                    self.assertContains(response, 'Available now')
                else:
                    self.assertContains(response, 'Back to dashboard')

    def test_base_uses_matching_bootstrap_bundle_and_runtime_toasts(self):
        ceo = User.objects.create_user(username='asset-smoke', password='test-pass-123', role=User.Role.CEO)
        self.client.force_login(ceo)
        response = self.client.get('/billing/')
        self.assertContains(response, 'bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js')
        self.assertContains(response, 'sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI')
        self.assertContains(response, 'class="toast-container"')
        self.assertContains(response, 'data-bs-target="#invoiceModal"')
        main_js = Path(finders.find('js/main.js')).read_text(encoding='utf-8')
        api_client = Path(finders.find('js/api/client.js')).read_text(encoding='utf-8')
        self.assertIn('window.JBSToast', main_js)
        self.assertIn('Interface library failed to load', main_js)
        self.assertIn('/api/v1${path} failed', api_client)

    def test_dashboard_is_the_single_role_aware_module_navigation(self):
        staff = User.objects.create_user(username='tile-staff', password='test-pass-123', role=User.Role.STAFF)
        self.client.force_login(staff)
        response = self.client.get('/')
        for path in ('/clients/', '/engagements/', '/sales/', '/billing/', '/expenses/', '/finance/', '/accounting/', '/products/', '/inventory/', '/purchasing/', '/tasks/', '/documents/', '/analytics/', '/alerts/', '/communication/', '/ai/', '/staff/', '/departments/', '/growth/'):
            with self.subTest(path=path):
                self.assertGreaterEqual(response.content.count(f'href="{path}"'.encode()), 1)
        self.assertNotContains(response, 'id="sidebar"')
        self.assertNotContains(response, 'Back to dashboard')
        self.assertContains(response, 'module-info-badge', count=24)
        self.assertContains(response, 'An invoice is a formal request asking a customer to pay')
        self.assertContains(response, 'aria-describedby="module-help-finance-1"')
        self.assertContains(response, 'group-growth')
        self.assertContains(response, 'Coming soon', count=5)
        self.assertNotContains(response, '/payroll/')
        self.assertNotContains(response, '/system-admin/')

        finance = self.client.get('/finance/')
        self.assertContains(finance, 'Back to dashboard')
        self.assertContains(finance, 'href="/"')
        self.assertNotContains(finance, 'id="sidebar"')

    def test_growth_marketing_placeholder_renders(self):
        user = User.objects.create_user(username='growth-user', password='test-pass-123')
        self.client.force_login(user)
        response = self.client.get('/growth/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Growth &amp; Marketing')
        self.assertContains(response, 'Coming soon')
        self.assertContains(response, 'Back to dashboard')
        self.assertNotContains(response, 'id="sidebar"')
