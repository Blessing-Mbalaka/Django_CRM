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
                if path == '/':
                    self.assertContains(response, 'CEO (Executive)')
                    self.assertContains(response, '/departments/')

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
