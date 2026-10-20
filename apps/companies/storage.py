import posixpath
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.views.static import serve

from .tenancy import current_company_id


class CompanyFileStorage(FileSystemStorage):
    def save(self, name, content, max_length=None):
        company_id = current_company_id()
        if company_id:
            prefix = f'companies/{company_id}/'
            if not name.startswith(prefix):
                name = prefix + name
        return super().save(name, content, max_length=max_length)


def company_media(request, path):
    if not request.user.is_authenticated:
        raise Http404
    path = posixpath.normpath(path.replace('\\', '/')).lstrip('/')
    company = request.company
    allowed = path.startswith(f'companies/{company.pk}/')
    if company.is_original and not path.startswith('companies/'):
        allowed = True  # Preserve access to legacy uploads for their original owner.
    if not allowed:
        from apps.academy.models import AcademyResource
        allowed = AcademyResource.objects.filter(resource_file=path, is_published=True).exists()
    if not allowed or '..' in Path(path).parts:
        raise Http404
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response['Cache-Control'] = 'private, no-store'
    return response
