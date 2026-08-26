import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Document, DocumentLibrary


class DocumentApiTests(APITestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.temp_media.cleanup)
        self.user = User.objects.create_user(username='docs', password='test-pass-123')
        self.other = User.objects.create_user(username='other-docs', password='test-pass-123')
        self.client.force_authenticate(self.user)
        self.library = DocumentLibrary.objects.create(name='Company Documents', owner=self.user)

    def test_create_document_and_upload_immutable_versions(self):
        response = self.client.post('/api/documents/', {'library': self.library.id, 'title': 'Contract'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        document_id = response.data['id']
        upload = SimpleUploadedFile('contract.txt', b'first version', content_type='text/plain')
        version = self.client.post('/api/document-versions/', {'document': document_id, 'file': upload}, format='multipart')
        self.assertEqual(version.status_code, status.HTTP_201_CREATED)
        self.assertEqual(version.data['version_number'], 1)
        self.assertEqual(len(version.data['checksum']), 64)

    def test_documents_are_private_to_library_owner(self):
        Document.objects.create(library=self.library, title='Private', owner=self.user)
        self.client.force_authenticate(self.other)
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_cannot_create_document_in_another_users_library(self):
        other_library = DocumentLibrary.objects.create(name='Other Files', owner=self.other)
        response = self.client.post('/api/documents/', {'library': other_library.id, 'title': 'Intrusion'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_versioned_api_route_is_available(self):
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
