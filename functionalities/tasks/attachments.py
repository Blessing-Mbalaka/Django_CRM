import hashlib
from pathlib import Path

from django.db import transaction

from apps.tasks.models import TaskAttachment
from functionalities.documents.validators import validate_upload


@transaction.atomic
def add_task_attachment(*, task, upload, user):
    validate_upload(upload)
    checksum = hashlib.sha256()
    for chunk in upload.chunks():
        checksum.update(chunk)
    upload.seek(0)
    return TaskAttachment.objects.create(
        task=task,
        file=upload,
        original_name=Path(upload.name).name,
        mime_type=getattr(upload, 'content_type', ''),
        size=upload.size,
        checksum=checksum.hexdigest(),
        uploaded_by=user,
    )
