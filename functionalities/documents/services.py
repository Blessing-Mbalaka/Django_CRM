import hashlib

from django.db import transaction

from apps.documents.models import DocumentActivity, DocumentVersion
from .validators import validate_upload


@transaction.atomic
def add_document_version(*, document, upload, user):
    validate_upload(upload)
    checksum = hashlib.sha256()
    for chunk in upload.chunks():
        checksum.update(chunk)
    upload.seek(0)
    latest = document.versions.order_by('-version_number').first()
    version = DocumentVersion.objects.create(
        document=document,
        version_number=(latest.version_number + 1) if latest else 1,
        file=upload,
        original_name=upload.name,
        mime_type=getattr(upload, 'content_type', ''),
        size=upload.size,
        checksum=checksum.hexdigest(),
        uploaded_by=user,
    )
    DocumentActivity.objects.create(
        document=document,
        actor=user,
        action='version_uploaded',
        detail={'version': version.version_number, 'name': version.original_name},
    )
    return version

