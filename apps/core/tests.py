from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase

from apps.accounts.models import User


class CoreLandingTests(TestCase):
    def test_authenticated_root_redirects_to_academy(self):
        user = User.objects.create_user(username='academy-landing', password='test-pass-123')
        self.client.force_login(user)

        response = self.client.get('/')

        self.assertRedirects(response, '/academy/', fetch_redirect_response=False)

    def test_anonymous_root_redirects_to_login(self):
        response = self.client.get('/')

        self.assertRedirects(response, '/accounts/login/?next=/', fetch_redirect_response=False)


class CEOApplicationSmokeTests(TestCase):
    def test_ceo_can_render_the_application_modules(self):
        ceo = User.objects.create_user(username='ceo-smoke', password='test-pass-123', role=User.Role.CEO)
        self.client.force_login(ceo)
        self.assertRedirects(self.client.get('/'), '/academy/', fetch_redirect_response=False)
        for path in [
            '/staff/', '/departments/', '/clients/', '/engagements/', '/finance/',
            '/alerts/', '/analytics/', '/communication/', '/documents/', '/tasks/',
            '/billing/', '/expenses/', '/products/', '/inventory/', '/purchasing/',
            '/sales/', '/accounting/',
            '/payroll/',
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                if path in ('/tasks/', '/inventory/'):
                    self.assertContains(response, 'id="sidebar"')
                    self.assertContains(response, 'href="/academy/#tools"')
                    self.assertNotContains(response, 'class="sme-branded-app"')
                elif path in ('/billing/', '/documents/'):
                    self.assertNotContains(response, 'id="crmSidebar"')
                    self.assertContains(response, 'Back to Business Tools')
                    self.assertContains(response, 'href="/academy/#tools"')
                    self.assertContains(response, 'class="sme-branded-app"')
                else:
                    self.assertContains(response, 'id="crmSidebar"')
                    self.assertContains(response, 'Back to Business Tools')
                    self.assertContains(response, 'href="/academy/#tools"')
                    self.assertContains(response, 'class="sme-branded-app crm-shell-enabled"')
                    self.assertContains(response, '/static/css/sme_brand.css')

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

    def test_academy_and_crm_split_primary_and_secondary_navigation(self):
        staff = User.objects.create_user(username='tile-staff', password='test-pass-123', role=User.Role.STAFF)
        self.client.force_login(staff)
        response = self.client.get('/academy/')
        for path in ('/billing/', '/inventory/', '/tasks/', '/growth/', '/clients/', '/documents/'):
            with self.subTest(path=path):
                self.assertContains(response, path)
        self.assertContains(response, 'id="sidebar"')
        self.assertNotContains(response, 'Back to Business Tools')
        self.assertContains(response, 'id="academy-tools-data"')
        self.assertContains(response, 'data-route="tools"')
        self.assertContains(response, 'data-route="diagnostics"')
        self.assertContains(response, 'Business Diagnostic')
        self.assertEqual(len(response.context['academy_tools']), 6)

        crm = self.client.get('/clients/')
        for path in ('/engagements/', '/sales/', '/expenses/', '/finance/', '/accounting/', '/products/', '/purchasing/', '/analytics/', '/alerts/', '/communication/', '/ai/', '/staff/', '/departments/'):
            with self.subTest(path=path):
                self.assertContains(crm, path)
        self.assertNotContains(crm, '/payroll/')
        self.assertNotContains(crm, '/system-admin/')
        self.assertContains(crm, 'id="crmSidebar"')

    def test_growth_marketing_workspace_renders(self):
        user = User.objects.create_user(username='growth-user', password='test-pass-123')
        self.client.force_login(user)
        response = self.client.get('/growth/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marketing &amp; Advertising')
        self.assertNotContains(response, 'Coming soon')
        self.assertContains(response, 'href="/academy/#tools"')
        self.assertContains(response, 'id="sidebar"')
        self.assertContains(response, 'id="marketing-config"')


class CRMShellNavigationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='crm-shell-user', role=User.Role.STAFF)
        self.client.force_login(self.user)

    def test_crm_contained_pages_render_persistent_sidebar(self):
        for path, active_label in (
            ('/clients/', 'Customers'),
            ('/engagements/', 'Engagements'),
            ('/finance/', 'Financial Overview'),
            ('/staff/', 'Staff'),
            ('/centres/', 'Departments'),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="crmSidebar"')
                self.assertContains(response, 'href="/academy/#tools"')
                self.assertContains(response, 'method="post" action="/accounts/logout/"')
                self.assertContains(response, f'<span>{active_label}</span>')
                self.assertContains(response, 'aria-current="page"')

    def test_standalone_and_account_pages_do_not_render_crm_sidebar(self):
        for path in ('/billing/', '/documents/', '/accounts/profile/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'id="crmSidebar"')

    def test_context_exposes_role_filtered_navigation_records(self):
        response = self.client.get('/clients/')

        self.assertTrue(response.context['use_crm_shell'])
        self.assertEqual(response.context['active_crm_namespace'], 'clients')
        groups = response.context['crm_navigation']
        self.assertTrue(groups)
        self.assertTrue(all(group['items'] for group in groups))
        self.assertTrue(all(
            item.get('label') and item.get('url') and item.get('svg_path')
            for group in groups for item in group['items']
        ))
        labels = [item['label'] for group in groups for item in group['items']]
        self.assertNotIn('Payroll Management', labels)
        self.assertNotIn('System Admin', labels)

    def test_administrator_context_includes_privileged_navigation(self):
        admin = User.objects.create_user(username='crm-shell-admin', role=User.Role.ADMIN)
        self.client.force_login(admin)

        response = self.client.get('/clients/')

        labels = [
            item['label']
            for group in response.context['crm_navigation']
            for item in group['items']
        ]
        self.assertIn('Payroll Management', labels)
        self.assertIn('System Admin', labels)
