from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.academy.models import CourseCategory, LearningPath


class AcademyManagementAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_user(
            username='academy-manager', password='test-pass', role='admin'
        )
        self.learner = user_model.objects.create_user(
            username='academy-learner', password='test-pass', role='staff'
        )

    def test_ordinary_user_cannot_list_or_create(self):
        self.client.force_authenticate(self.learner)
        url = reverse('academy-manage-course-category-list')
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(url, {'name': 'Finance', 'slug': 'finance'}).status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_crud_and_archived_record_remains_listed(self):
        self.client.force_authenticate(self.manager)
        url = reverse('academy-manage-course-category-list')
        created = self.client.post(url, {'name': 'Finance', 'slug': 'finance', 'position': 1})
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        detail = reverse('academy-manage-course-category-detail', args=[created.data['id']])
        updated = self.client.patch(detail, {'name': 'Business finance'})
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        CourseCategory.objects.get(pk=created.data['id']).courses.create(
            path=LearningPath.objects.create(
                slug='start', title='Start', business_stage='foundations'
            ),
            slug='cash-flow', title='Cash flow', description='Learn',
            instructor_name='Coach', duration_minutes=10,
        )
        removed = self.client.delete(detail)
        self.assertEqual(removed.status_code, status.HTTP_200_OK, removed.data)
        self.assertEqual(removed.data['action'], 'archived')
        self.assertFalse(CourseCategory.objects.get(pk=created.data['id']).is_active)
        ids = [item['id'] for item in self.client.get(url).data]
        self.assertIn(created.data['id'], ids)

    def test_all_management_collections_are_available(self):
        self.client.force_authenticate(self.manager)
        names = [
            'course-category', 'course-level', 'path', 'course', 'module',
            'resource-category', 'resource', 'diagnostic-category', 'diagnostic',
            'diagnostic-question', 'diagnostic-option', 'diagnostic-recommendation',
            'opportunity-category', 'funding', 'event-category', 'event', 'mentor',
            'forum-category', 'forum-post',
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(reverse(f'academy-manage-{name}-list'))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_duplicate_slug_has_field_error(self):
        CourseCategory.objects.create(name='Finance', slug='finance')
        self.client.force_authenticate(self.manager)
        response = self.client.post(reverse('academy-manage-course-category-list'), {
            'name': 'Other finance', 'slug': 'finance'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slug', response.data)

    def test_forum_management_is_moderation_only(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(reverse('academy-manage-forum-post-list'), {
            'title': 'Managers must not impersonate authors', 'body': 'No.'
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
