from apps.companies.models import CompanyOwnedModel
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentLibrary(CompanyOwnedModel):
    class Scope(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        TEAM = 'team', 'Team'
        ORGANISATION = 'organisation', 'Organisation'

    name = models.CharField(max_length=160)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.PERSONAL)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_libraries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'owner', 'name'], name='documents_unique_library_name_per_owner'),
        ]

    def __str__(self):
        return self.name


class Folder(CompanyOwnedModel):
    library = models.ForeignKey(DocumentLibrary, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=160)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_folders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'library', 'parent', 'name'], name='documents_unique_folder_name'),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.parent_id and self.parent.library_id != self.library_id:
            raise ValidationError({'parent': 'Parent folder must belong to the same library.'})
        ancestor = self.parent
        while ancestor:
            if ancestor.pk == self.pk:
                raise ValidationError({'parent': 'A folder cannot contain itself.'})
            ancestor = ancestor.parent

    def __str__(self):
        return self.name


class Document(CompanyOwnedModel):
    class Classification(models.TextChoices):
        PUBLIC = 'public', 'Public'
        INTERNAL = 'internal', 'Internal'
        CONFIDENTIAL = 'confidential', 'Confidential'
        RESTRICTED = 'restricted', 'Restricted'

    library = models.ForeignKey(DocumentLibrary, on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    title = models.CharField(max_length=255)
    classification = models.CharField(max_length=20, choices=Classification.choices, default=Classification.INTERNAL)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_documents')
    client = models.ForeignKey('clients.Client', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    engagement = models.ForeignKey('engagements.Engagement', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    is_favourite = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def latest_version(self):
        return self.versions.order_by('-version_number').first()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def __str__(self):
        return self.title


def document_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f'documents/{instance.document_id}/{instance.version_number}{suffix}'


class DocumentVersion(CompanyOwnedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to=document_upload_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    checksum = models.CharField(max_length=64, db_index=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='document_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        constraints = [
            models.UniqueConstraint(fields=['company', 'document', 'version_number'], name='documents_unique_version_number'),
        ]

    def __str__(self):
        return f'{self.document.title} v{self.version_number}'


class DocumentActivity(CompanyOwnedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    action = models.CharField(max_length=40)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

