from django.contrib.staticfiles import finders
from django.test import TestCase

from apps.accounts.models import User


class AcademyCoursePageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='course-page-user', password='test-pass-123')

    def test_academy_page_requires_authentication(self):
        response = self.client.get('/academy/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_academy_page_loads_preserved_styles_and_api_frontend(self):
        self.client.force_login(self.user)

        response = self.client.get('/academy/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/static/sme/shared/css/inventory.css')
        self.assertContains(response, '/static/sme/shared/css/knowledge-hub.css')
        self.assertContains(response, '/static/sme/academy/css/style.css')
        self.assertContains(response, '/static/sme/academy/js/api.js')
        self.assertContains(response, '/static/sme/academy/js/course-page.js')
        self.assertNotContains(response, 'js/data.js')

    def test_academy_page_allows_only_supported_youtube_frame_origins(self):
        self.client.force_login(self.user)

        response = self.client.get('/academy/')

        self.assertEqual(
            response.headers['Content-Security-Policy'],
            "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
        )

    def test_academy_static_assets_are_discoverable(self):
        for path in (
            'sme/shared/css/inventory.css',
            'sme/shared/css/knowledge-hub.css',
            'sme/academy/css/style.css',
            'sme/academy/js/api.js',
            'sme/academy/js/course-page.js',
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))
