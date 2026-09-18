from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AcademyManagementViewTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.manager = users.objects.create_user(username='manager-view', password='pass', role='admin')
        self.learner = users.objects.create_user(username='learner-view', password='pass', role='staff')

    def test_manager_receives_workspace_configuration_and_dialog(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('academy:index'))
        self.assertContains(response, 'id="academy-management-data"')
        self.assertContains(response, 'id="academyManageDialog"')
        self.assertContains(response, 'academy/css/admin.css')
        self.assertContains(response, 'academy-admin-api.js')
        self.assertContains(response, '/api/v1/academy/manage/courses/')
        self.assertContains(response, 'data-manage-context="course"')

    def test_learner_does_not_receive_management_assets(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse('academy:index'))
        self.assertNotContains(response, 'academy-management-data')
        self.assertNotContains(response, 'academyManageDialog')
        self.assertNotContains(response, 'academy-admin.js')
