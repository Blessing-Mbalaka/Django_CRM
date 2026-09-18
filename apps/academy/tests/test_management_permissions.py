from django.test import TestCase

from apps.accounts.models import User


class AcademyManagementPermissionTests(TestCase):
    def test_only_approved_manager_types_see_manage_academy(self):
        cases = [
            ('learner', User.Role.STAFF, False, False, False),
            ('administrator', User.Role.ADMIN, False, False, True),
            ('ceo', User.Role.CEO, False, False, True),
            ('django-staff', User.Role.STAFF, True, False, True),
            ('superuser', User.Role.STAFF, True, True, True),
        ]
        for username, role, is_staff, is_superuser, allowed in cases:
            with self.subTest(username=username):
                user = User.objects.create_user(
                    username=username,
                    password='test-pass-123',
                    role=role,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                )
                self.client.force_login(user)
                response = self.client.get('/academy/')
                self.assertEqual(response.status_code, 200)
                if allowed:
                    self.assertContains(response, 'data-route="manage"')
                else:
                    self.assertNotContains(response, 'data-route="manage"')
