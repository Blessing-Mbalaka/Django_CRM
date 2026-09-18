from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from apps.academy.models import Course, CourseModule, LearningPath
from apps.academy.validators import extract_youtube_video_id


class YouTubeUrlValidationTests(SimpleTestCase):
    def test_supported_youtube_urls_return_video_id(self):
        supported = {
            'https://www.youtube.com/watch?v=M7lc1UVf-VE': 'M7lc1UVf-VE',
            'https://youtu.be/M7lc1UVf-VE?t=12': 'M7lc1UVf-VE',
            'https://www.youtube.com/embed/M7lc1UVf-VE': 'M7lc1UVf-VE',
            'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE': 'M7lc1UVf-VE',
        }

        for url, expected in supported.items():
            with self.subTest(url=url):
                self.assertEqual(extract_youtube_video_id(url), expected)

    def test_unsupported_host_is_rejected(self):
        with self.assertRaisesMessage(ValidationError, 'supported YouTube URL'):
            extract_youtube_video_id('https://example.com/embed/M7lc1UVf-VE')

    def test_malformed_video_id_is_rejected(self):
        with self.assertRaisesMessage(ValidationError, 'valid YouTube video ID'):
            extract_youtube_video_id('https://www.youtube.com/watch?v=not-valid')


class AcademyContentModelTests(TestCase):
    def setUp(self):
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
            instructor_name='Academy facilitator',
            level=Course.Level.BEGINNER,
            duration_minutes=60,
            position=1,
            is_published=True,
        )

    def test_course_module_embed_url_uses_validated_video_and_origin(self):
        module = CourseModule.objects.create(
            course=self.course,
            title='Introduction',
            module_type=CourseModule.Type.VIDEO,
            video_url='https://youtu.be/M7lc1UVf-VE',
            position=1,
            is_published=True,
        )

        self.assertEqual(module.youtube_video_id, 'M7lc1UVf-VE')
        self.assertEqual(
            module.youtube_embed_url('https://academy.example.org'),
            'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?origin=https%3A%2F%2Facademy.example.org',
        )

    def test_video_module_requires_a_video_url(self):
        module = CourseModule(
            course=self.course,
            title='Introduction',
            module_type=CourseModule.Type.VIDEO,
            position=1,
        )

        with self.assertRaisesMessage(ValidationError, 'Video modules require a YouTube URL'):
            module.full_clean()

    def test_non_video_module_rejects_a_video_url(self):
        module = CourseModule(
            course=self.course,
            title='Reading',
            module_type=CourseModule.Type.ARTICLE,
            video_url='https://youtu.be/M7lc1UVf-VE',
            position=1,
        )

        with self.assertRaisesMessage(ValidationError, 'only allowed for video modules'):
            module.full_clean()
