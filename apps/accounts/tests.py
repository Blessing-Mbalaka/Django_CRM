from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import TestCase, override_settings
from io import StringIO

from .models import User
from jbs_crm.settings import development


@override_settings(DEBUG=True)
class DevelopmentLoginPageTests(TestCase):
    def test_local_theme_stylesheet_is_served(self):
        self.assertTrue(development.DEBUG)
        self.assertIsNotNone(finders.find('css/uj_theme.css'))

    def test_login_page_shows_usable_demo_accounts_in_development(self):
        call_command('seed_users', verbosity=0, stdout=StringIO())

        response = self.client.get('/accounts/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo accounts')
        self.assertContains(response, 'ndlamini')
        self.assertContains(response, 'mradebe')
        self.assertContains(response, 'zmahlangu')
        self.assertContains(response, 'JBS@2026!')
        self.assertContains(response, 'data-demo-username="ndlamini"')

        login_response = self.client.post('/accounts/login/', {
            'company': 'original',
            'username': 'ndlamini',
            'password': 'JBS@2026!',
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, '/academy/')

    @override_settings(DEBUG=False)
    def test_login_page_never_exposes_demo_credentials_outside_development(self):
        response = self.client.get('/accounts/login/')

        self.assertNotContains(response, 'Demo accounts')
        self.assertNotContains(response, 'JBS@2026!')


class SeedUsersCommandTests(TestCase):
    def test_reset_demo_passwords_restores_existing_test_account(self):
        user = User.objects.create_user(
            username='ndlamini', password='changed-password', first_name='Nomsa',
            last_name='Dlamini', role=User.Role.CEO,
        )

        call_command('seed_users', reset_demo_passwords=True, verbosity=0, stdout=StringIO())

        user.refresh_from_db()
        self.assertTrue(user.check_password('JBS@2026!'))
