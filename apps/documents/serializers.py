from rest_framework import serializers

from functionalities.documents.services import add_document_version
from .models import Document, DocumentLibrary, DocumentVersion, Folder


class DocumentLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentLibrary
        fields = ['id', 'name', 'scope', 'owner', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'library', 'parent', 'name', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate(self, attrs):
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        library = attrs.get('library', getattr(self.instance, 'library', None))
        request = self.context.get('request')
        if request and library and library.owner_id != request.user.id:
            raise serializers.ValidationError({'library': 'You do not have access to this library.'})
        if parent and library and parent.library_id != library.id:
            raise serializers.ValidationError({'parent': 'Parent folder must belong to the same library.'})
        return attrs


class DocumentVersionSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'version_number', 'file', 'original_name', 'mime_type', 'size', 'checksum', 'uploaded_by', 'uploaded_by_name', 'created_at']
        read_only_fields = ['id', 'version_number', 'original_name', 'mime_type', 'size', 'checksum', 'uploaded_by', 'created_at']

    def create(self, validated_data):
        upload = validated_data.pop('file')
        return add_document_version(document=validated_data['document'], upload=upload, user=self.context['request'].user)

    def validate_document(self, document):
        if document.library.owner_id != self.context['request'].user.id:
            raise serializers.ValidationError('You do not have access to this document.')
        return document


class DocumentSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'library', 'folder', 'title', 'classification', 'owner', 'owner_name', 'client', 'engagement', 'is_favourite', 'is_deleted', 'deleted_at', 'latest_version', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'is_deleted', 'deleted_at', 'created_at', 'updated_at']

    def get_latest_version(self, obj):
        version = obj.latest_version
        return DocumentVersionSerializer(version, context=self.context).data if version else None

    def validate(self, attrs):
        folder = attrs.get('folder', getattr(self.instance, 'folder', None))
        library = attrs.get('library', getattr(self.instance, 'library', None))
        request = self.context.get('request')
        if request and library and library.owner_id != request.user.id:
            raise serializers.ValidationError({'library': 'You do not have access to this library.'})
        if folder and library and folder.library_id != library.id:
            raise serializers.ValidationError({'folder': 'Folder must belong to the selected library.'})
        return attrs
