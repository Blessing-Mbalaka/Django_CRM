from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Centre


class DepartmentNamingTests(APITestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(username='ceo', password='test-pass-123', role=User.Role.CEO)
        self.client.force_authenticate(self.ceo)

    def test_ceo_and_department_are_canonical_labels(self):
        self.assertEqual(self.ceo.get_role_display(), 'CEO (Executive)')
        response = self.client.post('/api/v1/departments/', {'name': 'Operations', 'code': 'OPS', 'is_active': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Centre._meta.verbose_name, 'Department')

    def test_department_and_legacy_centre_routes_both_work(self):
        Centre.objects.create(name='Finance', code='FIN')
        self.assertEqual(self.client.get('/api/v1/departments/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/centres/').status_code, status.HTTP_200_OK)
        self.client.force_login(self.ceo)
        department_page = self.client.get('/departments/')
        self.assertEqual(department_page.status_code, status.HTTP_200_OK)
        self.assertContains(department_page, 'Departments')
        self.assertNotContains(department_page, '>Centres<')
        self.assertEqual(self.client.get('/centres/').status_code, status.HTTP_200_OK)
