from django.contrib import admin
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.academy.models import Course, CourseModule, LearningPath


class AcademyAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='academy-admin',
            email='academy-admin@example.com',
            password='test-pass-123',
        )
        self.client.force_login(self.admin_user)

    def test_academy_content_models_are_registered(self):
        self.assertIn(LearningPath, admin.site._registry)
        self.assertIn(Course, admin.site._registry)

    def test_course_add_page_exposes_inline_modules(self):
        response = self.client.get(reverse('admin:academy_course_add'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Course modules')
        self.assertContains(response, 'Video url')
        self.assertContains(response, 'Module type')

    def test_module_admin_is_not_a_separate_top_level_screen(self):
        self.assertNotIn(CourseModule, admin.site._registry)
