from django.contrib import admin

from .models import Document, DocumentActivity, DocumentLibrary, DocumentVersion, Folder

admin.site.register([DocumentLibrary, Folder, Document, DocumentVersion, DocumentActivity])

