from django.test import TestCase

from apps.accounts.models import User
from apps.academy.models import (
    Certificate,
    Course,
    CourseEnrollment,
    CourseLevel,
    CourseModule,
    LearningPath,
)
from apps.academy.services import complete_module, submit_quiz


class CourseCompletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='test-pass-123')
        path = LearningPath.objects.create(
            slug='completion', title='Completion', business_stage='build', is_published=True
        )
        level = CourseLevel.objects.create(slug='starter', name='Starter', is_active=True)
        self.course = Course.objects.create(
            path=path,
            level_config=level,
            slug='completion-course',
            title='Completion course',
            description='Test completion.',
            instructor_name='Facilitator',
            duration_minutes=30,
            passing_grade=75,
            certificate_enabled=True,
            is_published=True,
        )
        self.article = CourseModule.objects.create(
            course=self.course, title='Read', module_type='article', position=1,
            is_required=True, is_published=True,
        )
        self.quiz = CourseModule.objects.create(
            course=self.course, title='Quiz', module_type='quiz', position=2,
            prompt='Choose correctly', quiz_options=['Correct', 'Wrong'], correct_option=0,
            is_required=True, is_published=True,
        )
        self.enrollment = CourseEnrollment.objects.create(user=self.user, course=self.course)

    def test_certificate_is_issued_only_after_required_modules_and_passing_quiz(self):
        complete_module(self.enrollment, self.article)
        submit_quiz(self.enrollment, self.quiz, selected_option=1)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, CourseEnrollment.Status.FAILED)
        self.assertFalse(Certificate.objects.filter(enrollment=self.enrollment).exists())

        submit_quiz(self.enrollment, self.quiz, selected_option=0)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, CourseEnrollment.Status.PASSED)
        self.assertEqual(self.enrollment.final_grade, 100)
        certificate = Certificate.objects.get(enrollment=self.enrollment)
        self.assertEqual(certificate.learner_name, self.user.get_full_name() or self.user.username)
        self.assertEqual(certificate.course_title, self.course.title)

    def test_completion_is_idempotent(self):
        complete_module(self.enrollment, self.article)
        complete_module(self.enrollment, self.article)
        self.assertEqual(self.enrollment.module_progress.count(), 1)
