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
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                if path == '/':
                    self.assertContains(response, 'CEO (Executive)')
                    self.assertContains(response, '/departments/')
