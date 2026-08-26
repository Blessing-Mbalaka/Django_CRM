from django.test import TestCase

from apps.accounts.models import User


class DeanApplicationSmokeTests(TestCase):
    def test_dean_can_render_the_application_modules(self):
        dean = User.objects.create_user(username='dean-smoke', password='test-pass-123', role=User.Role.DEAN)
        self.client.force_login(dean)
        for path in [
            '/', '/staff/', '/centres/', '/clients/', '/engagements/', '/finance/',
            '/alerts/', '/analytics/', '/communication/', '/documents/', '/tasks/',
            '/billing/', '/expenses/', '/products/', '/inventory/', '/purchasing/',
            '/sales/', '/accounting/',
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
