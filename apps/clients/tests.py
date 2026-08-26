from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.centres.models import Centre


class DepartmentApiAliasTests(APITestCase):
    def test_client_accepts_and_returns_department_name(self):
        ceo = User.objects.create_user(username='client-ceo', password='test-pass-123', role=User.Role.CEO)
        department = Centre.objects.create(name='Sales', code='SAL')
        self.client.force_authenticate(ceo)
        response = self.client.post('/api/v1/clients/', {'name': 'Department Client', 'department': department.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['department'], department.id)
        self.assertEqual(response.data['department_name'], 'Sales')
