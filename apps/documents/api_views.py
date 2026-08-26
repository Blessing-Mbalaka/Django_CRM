from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Document, DocumentLibrary, DocumentVersion, Folder
from .serializers import DocumentLibrarySerializer, DocumentSerializer, DocumentVersionSerializer, FolderSerializer


class OwnedResourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]


class DocumentLibraryViewSet(OwnedResourceViewSet):
    serializer_class = DocumentLibrarySerializer

    def get_queryset(self):
        return DocumentLibrary.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        if instance.documents.exists() or instance.folders.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('A non-empty document library cannot be deleted.')
        instance.delete()


class FolderViewSet(OwnedResourceViewSet):
    serializer_class = FolderSerializer

    def get_queryset(self):
        return Folder.objects.filter(library__owner=self.request.user).select_related('library', 'parent')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DocumentViewSet(OwnedResourceViewSet):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = Document.objects.filter(library__owner=self.request.user).select_related('library', 'folder', 'owner', 'client', 'engagement')
        if self.request.query_params.get('trash') == 'true':
            return qs.filter(deleted_at__isnull=False)
        return qs.filter(deleted_at__isnull=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        document = Document.objects.filter(library__owner=request.user, pk=pk).first()
        if not document:
            return Response(status=status.HTTP_404_NOT_FOUND)
        document.deleted_at = None
        document.save(update_fields=['deleted_at', 'updated_at'])
        return Response(self.get_serializer(document).data)


class DocumentVersionViewSet(OwnedResourceViewSet):
    serializer_class = DocumentVersionSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return DocumentVersion.objects.filter(document__library__owner=self.request.user).select_related('document', 'uploaded_by')
