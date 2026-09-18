from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.academy.models import Certificate, Course, CourseEnrollment, LearningPath


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
        self.assertNotContains(response, 'bootstrap-icons')
        self.assertContains(response, '/static/sme/shared/css/inventory.css')
        self.assertContains(response, '/static/sme/shared/css/knowledge-hub.css')
        self.assertContains(response, '/static/sme/academy/css/style.css')
        self.assertContains(response, '/static/sme/academy/js/api.js')
        self.assertContains(response, '/static/sme/academy/js/course-page.js')
        self.assertContains(response, 'class="nav-icon"')
        self.assertContains(response, reverse('core:dashboard'))
        self.assertNotContains(response, 'js/data.js')
        for endpoint in (
            '/api/v1/academy/enrollments/', '/api/v1/academy/resources/',
            '/api/v1/academy/diagnostics/', '/api/v1/academy/funding/',
            '/api/v1/academy/events/', '/api/v1/academy/mentors/',
            '/api/v1/academy/forum/posts/',
        ):
            with self.subTest(endpoint=endpoint):
                self.assertContains(response, endpoint)
        for navigation_item in (
            'Dashboard', 'My Learning', 'Learning Paths', 'Courses',
            'Business Diagnostic', 'Templates &amp; Resources', 'Business Tools',
            'Mentorship', 'Community', 'Funding', 'Events', 'Growth',
            'Certificates', 'My Profile', 'Settings',
        ):
            with self.subTest(navigation_item=navigation_item):
                self.assertContains(response, navigation_item)
        self.assertContains(response, 'id="academy-tools-data"')
        self.assertContains(response, '"url": "/billing/"')
        self.assertContains(response, '"svg_path"')
        self.assertNotContains(response, '127.0.0.1:8023')

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

    def test_learner_can_print_own_certificate_but_not_another_users(self):
        other = User.objects.create_user(username='other-learner', password='test-pass-123')
        path = LearningPath.objects.create(slug='certificate', title='Certificate', business_stage='build')
        course = Course.objects.create(
            path=path, slug='cert-course', title='Certificate course', description='Done',
            instructor_name='Coach', duration_minutes=10,
        )
        enrollment = CourseEnrollment.objects.create(user=self.user, course=course, status='passed')
        certificate = Certificate.objects.create(
            enrollment=enrollment, learner_name='Course Page User', course_title=course.title, grade=100,
        )

        self.client.force_login(other)
        denied = self.client.get(f'/academy/certificates/{certificate.verification_id}/')
        self.client.force_login(self.user)
        allowed = self.client.get(f'/academy/certificates/{certificate.verification_id}/')

        self.assertEqual(denied.status_code, 404)
        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, str(certificate.verification_id))
