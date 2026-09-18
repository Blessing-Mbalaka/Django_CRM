from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Course, CourseModule, LearningPath
from .serializers import CourseDetailSerializer, CourseListSerializer, LearningPathSummarySerializer


class LearningPathViewSet(ReadOnlyModelViewSet):
    serializer_class = LearningPathSummarySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    queryset = LearningPath.objects.filter(is_published=True)


class CourseViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_serializer_class(self):
        return CourseDetailSerializer if self.action == 'retrieve' else CourseListSerializer

    def get_queryset(self):
        published_modules = CourseModule.objects.filter(is_published=True).order_by('position', 'id')
        queryset = Course.objects.filter(
            is_published=True,
            path__is_published=True,
        ).select_related('path').prefetch_related(
            Prefetch('modules', queryset=published_modules, to_attr='published_modules')
        )
        if path_slug := self.request.query_params.get('path'):
            queryset = queryset.filter(path__slug=path_slug)
        return queryset

