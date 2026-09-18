from django.test import TestCase

from apps.accounts.models import User
from apps.academy.management_services import safe_remove
from apps.academy.models import (
    AcademyResource, Course, CourseEnrollment, Diagnostic, DiagnosticCategory,
    DiagnosticQuestion, DiagnosticSubmission, LearningPath,
)


class AcademySafeRemovalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='archive-user', password='test-pass-123')
        self.path = LearningPath.objects.create(
            slug='archive-path', title='Archive path', business_stage='build', is_published=True,
        )
        self.course = Course.objects.create(
            path=self.path, slug='archive-course', title='Archive course', description='Course',
            instructor_name='Coach', duration_minutes=30, is_published=True,
        )

    def test_referenced_course_is_unpublished_without_losing_enrollment(self):
        enrollment = CourseEnrollment.objects.create(user=self.user, course=self.course)

        result = safe_remove(self.course)

        self.course.refresh_from_db()
        self.assertEqual(result.action, 'archived')
        self.assertFalse(self.course.is_published)
        self.assertTrue(CourseEnrollment.objects.filter(pk=enrollment.pk).exists())

    def test_unused_resource_is_deleted(self):
        resource = AcademyResource.objects.create(slug='remove-me', title='Remove me')
        resource_id = resource.pk

        result = safe_remove(resource)

        self.assertEqual(result.action, 'deleted')
        self.assertFalse(AcademyResource.objects.filter(pk=resource_id).exists())

    def test_question_from_attempted_diagnostic_is_deactivated(self):
        category = DiagnosticCategory.objects.create(name='Finance', slug='finance')
        diagnostic = Diagnostic.objects.create(slug='health', title='Health', is_published=True)
        question = DiagnosticQuestion.objects.create(
            diagnostic=diagnostic, category=category, prompt='How healthy?', position=1,
        )
        DiagnosticSubmission.objects.create(
            user=self.user, diagnostic=diagnostic, diagnostic_version=1,
            answers={}, category_scores={}, recommendations=[], total_score=0,
        )

        result = safe_remove(question)

        question.refresh_from_db()
        self.assertEqual(result.action, 'archived')
        self.assertFalse(question.is_active)
