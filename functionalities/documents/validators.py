from django.core.exceptions import ValidationError


MAX_DOCUMENT_SIZE = 25 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'text/plain',
}


def validate_upload(upload):
    if upload.size > MAX_DOCUMENT_SIZE:
        raise ValidationError('Files may not exceed 25 MB.')
    mime_type = getattr(upload, 'content_type', '')
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError('This file type is not supported.')

