from django.core.management import call_command
from django.test import TestCase

from apps.academy.models import Course, CourseCategory, CourseLevel, CourseModule, LearningPath


class SeedAcademyCommandTests(TestCase):
    def test_seed_is_idempotent_and_preserves_admin_edits(self):
        call_command('seed_academy', verbosity=0)

        self.assertEqual(LearningPath.objects.count(), 8)
        self.assertEqual(Course.objects.count(), 72)
        self.assertEqual(CourseModule.objects.count(), 648)
        self.assertEqual(CourseCategory.objects.count(), 8)
        self.assertEqual(CourseLevel.objects.count(), 2)
        course = Course.objects.get(slug='idea')
        self.assertEqual(course.title, 'Idea Generation for South African SMEs')
        self.assertEqual(course.modules.filter(is_published=True).count(), 9)
        self.assertIsNotNone(course.category)
        self.assertIsNotNone(course.level_config)

        course.title = 'Edited by an administrator'
        course.save(update_fields=['title'])
        call_command('seed_academy', verbosity=0)

        self.assertEqual(LearningPath.objects.count(), 8)
        self.assertEqual(Course.objects.count(), 72)
        self.assertEqual(CourseModule.objects.count(), 648)
        course.refresh_from_db()
        self.assertEqual(course.title, 'Edited by an administrator')
