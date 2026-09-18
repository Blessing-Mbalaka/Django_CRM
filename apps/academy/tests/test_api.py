from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.academy.models import Course, CourseModule, LearningPath


class AcademyCatalogueApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='academy-learner', password='test-pass-123')
        self.client.force_authenticate(self.user)
        self.path = LearningPath.objects.create(
            slug='foundations',
            title='Entrepreneurship Foundations',
            business_stage=LearningPath.BusinessStage.FOUNDATIONS,
            position=1,
            is_published=True,
        )
        self.course = Course.objects.create(
            path=self.path,
            slug='idea-generation',
            title='Idea Generation',
            description='Choose one customer problem to investigate.',
            learning_outcome='Evaluate a business idea.',
            instructor_name='Academy facilitator',
            level=Course.Level.BEGINNER,
            duration_minutes=60,
            position=2,
            is_published=True,
        )
        CourseModule.objects.create(
            course=self.course,
            title='Second lesson',
            module_type=CourseModule.Type.ARTICLE,
            body='Read this second.',
            position=2,
            is_published=True,
        )
        CourseModule.objects.create(
            course=self.course,
            title='Video introduction',
            module_type=CourseModule.Type.VIDEO,
            video_url='https://www.youtube.com/watch?v=M7lc1UVf-VE',
            position=1,
            is_published=True,
        )
        CourseModule.objects.create(
            course=self.course,
            title='Draft lesson',
            module_type=CourseModule.Type.ARTICLE,
            body='Do not expose this.',
            position=3,
            is_published=False,
        )

    def test_paths_and_courses_return_only_published_content(self):
        draft_path = LearningPath.objects.create(
            slug='draft-path',
            title='Draft path',
            business_stage=LearningPath.BusinessStage.BUILD,
            position=2,
            is_published=False,
        )
        Course.objects.create(
            path=draft_path,
            slug='draft-course',
            title='Draft course',
            description='Hidden',
            instructor_name='Hidden',
            duration_minutes=30,
            position=1,
            is_published=True,
        )

        paths = self.client.get('/api/v1/academy/paths/')
        courses = self.client.get('/api/v1/academy/courses/')

        self.assertEqual(paths.status_code, status.HTTP_200_OK)
        self.assertEqual([item['slug'] for item in paths.data['results']], ['foundations'])
        self.assertEqual(courses.status_code, status.HTTP_200_OK)
        self.assertEqual([item['slug'] for item in courses.data['results']], ['idea-generation'])

    def test_courses_can_be_filtered_by_path_slug(self):
        response = self.client.get('/api/v1/academy/courses/?path=foundations')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['path']['slug'], 'foundations')

    @override_settings(ALLOWED_HOSTS=['academy.example.org', 'testserver'])
    def test_course_detail_has_ordered_published_modules_and_request_origin(self):
        response = self.client.get(
            '/api/v1/academy/courses/idea-generation/',
            HTTP_HOST='academy.example.org',
            secure=True,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [module['title'] for module in response.data['modules']],
            ['Video introduction', 'Second lesson'],
        )
        self.assertEqual(
            response.data['modules'][0]['video_embed_url'],
            'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?origin=https%3A%2F%2Facademy.example.org',
        )

    def test_anonymous_user_cannot_read_catalogue(self):
        self.client.force_authenticate(None)

        response = self.client.get('/api/v1/academy/courses/')

        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_api_root_advertises_academy_catalogue(self):
        response = self.client.get('/api/v1/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['endpoints']['academy_paths'].endswith('/api/v1/academy/paths/'))
        self.assertTrue(response.data['endpoints']['academy_courses'].endswith('/api/v1/academy/courses/'))
