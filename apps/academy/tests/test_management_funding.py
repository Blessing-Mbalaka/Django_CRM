from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.academy.models import FundingOpportunity


class FundingCSVManagementTests(APITestCase):
    def setUp(self):
        users = get_user_model()
        self.manager = users.objects.create_user(username='csv-manager', password='pass', role='admin')
        self.learner = users.objects.create_user(username='csv-learner', password='pass', role='staff')
        self.base = reverse('academy-manage-funding-list')
        self.csv = (
            'slug,title,provider,category,description,eligibility,opens_on,closes_on,application_url,contact_email,is_published\n'
            'growth-fund,Growth Fund,Agency,,Support,SMEs,2026-01-01,2026-12-31,https://example.com/apply,help@example.com,true\n'
        ).encode()

    def upload(self, action):
        return self.client.post(f'{self.base}{action}/', {
            'file': SimpleUploadedFile('funding.csv', self.csv, content_type='text/csv')
        }, format='multipart')

    def test_template_preview_and_atomic_import(self):
        self.client.force_authenticate(self.manager)
        template = self.client.get(f'{self.base}csv-template/')
        self.assertEqual(template.status_code, 200)
        self.assertIn('funding-opportunities-template.csv', template['Content-Disposition'])
        preview = self.upload('preview-csv')
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertTrue(preview.data['is_valid'])
        self.assertEqual(FundingOpportunity.objects.count(), 0)
        imported = self.upload('import-csv')
        self.assertEqual(imported.status_code, 200, imported.data)
        self.assertEqual(imported.data['imported'], 1)
        self.assertTrue(FundingOpportunity.objects.filter(slug='growth-fund').exists())

    def test_learner_cannot_import(self):
        self.client.force_authenticate(self.learner)
        self.assertEqual(self.upload('import-csv').status_code, 403)
