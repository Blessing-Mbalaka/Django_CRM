from django.test import TestCase

from apps.accounts.models import User


class ProductPageTests(TestCase):
    def test_catalogue_page_renders_for_authenticated_user(self):
        user = User.objects.create_user(username='catalogue-user', password='test-pass-123')
        self.client.force_login(user)
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Products &amp; Services')

