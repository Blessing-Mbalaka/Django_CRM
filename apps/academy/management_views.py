import csv
import io

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .funding_import import FUNDING_CSV_HEADERS, import_funding_csv
from .management_serializers import *
from .management_services import safe_remove
from .models import *
from .permissions import IsAcademyManager


class SafeDestroyModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAcademyManager]
    pagination_class = None

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        result = safe_remove(instance)
        if result.action == 'deleted':
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'action': result.action, 'item': self.get_serializer(result.instance).data})


class CourseCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = CourseCategory.objects.all(); serializer_class = CourseCategoryManagementSerializer
class CourseLevelManagementViewSet(SafeDestroyModelViewSet):
    queryset = CourseLevel.objects.all(); serializer_class = CourseLevelManagementSerializer
class LearningPathManagementViewSet(SafeDestroyModelViewSet):
    queryset = LearningPath.objects.all(); serializer_class = LearningPathManagementSerializer
class CourseManagementViewSet(SafeDestroyModelViewSet):
    queryset = Course.objects.select_related('path', 'category', 'level_config').all(); serializer_class = CourseManagementSerializer
class CourseModuleManagementViewSet(SafeDestroyModelViewSet):
    serializer_class = CourseModuleManagementSerializer
    def get_queryset(self):
        qs = CourseModule.objects.select_related('course').all()
        return qs.filter(course_id=self.request.query_params['course']) if self.request.query_params.get('course') else qs
class ResourceCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = AcademyResourceCategory.objects.all(); serializer_class = ResourceCategoryManagementSerializer
class AcademyResourceManagementViewSet(SafeDestroyModelViewSet):
    queryset = AcademyResource.objects.select_related('category').all(); serializer_class = AcademyResourceManagementSerializer
class DiagnosticCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = DiagnosticCategory.objects.all(); serializer_class = DiagnosticCategoryManagementSerializer
class DiagnosticManagementViewSet(SafeDestroyModelViewSet):
    queryset = Diagnostic.objects.all(); serializer_class = DiagnosticManagementSerializer
class DiagnosticQuestionManagementViewSet(SafeDestroyModelViewSet):
    serializer_class = DiagnosticQuestionManagementSerializer
    def get_queryset(self):
        qs = DiagnosticQuestion.objects.select_related('diagnostic', 'category').all()
        return qs.filter(diagnostic_id=self.request.query_params['diagnostic']) if self.request.query_params.get('diagnostic') else qs
class DiagnosticOptionManagementViewSet(SafeDestroyModelViewSet):
    serializer_class = DiagnosticOptionManagementSerializer
    def get_queryset(self):
        qs = DiagnosticOption.objects.select_related('question').all()
        return qs.filter(question_id=self.request.query_params['question']) if self.request.query_params.get('question') else qs
class DiagnosticRecommendationManagementViewSet(SafeDestroyModelViewSet):
    serializer_class = DiagnosticRecommendationManagementSerializer
    def get_queryset(self):
        qs = DiagnosticRecommendation.objects.select_related('diagnostic', 'category', 'course').all()
        return qs.filter(diagnostic_id=self.request.query_params['diagnostic']) if self.request.query_params.get('diagnostic') else qs
class OpportunityCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = OpportunityCategory.objects.all(); serializer_class = OpportunityCategoryManagementSerializer


class FundingOpportunityManagementViewSet(SafeDestroyModelViewSet):
    queryset = FundingOpportunity.objects.select_related('category').all(); serializer_class = FundingOpportunityManagementSerializer

    @action(detail=False, methods=['get'], url_path='csv-template')
    def csv_template(self, request):
        output = io.StringIO(); csv.writer(output).writerow(FUNDING_CSV_HEADERS)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="funding-opportunities-template.csv"'
        return response

    def _import_response(self, request, commit):
        upload = request.FILES.get('file')
        if not upload:
            return Response({'file': ['Choose a CSV file.']}, status=status.HTTP_400_BAD_REQUEST)
        result = import_funding_csv(upload, commit=commit)
        code = status.HTTP_200_OK if result.is_valid else status.HTTP_400_BAD_REQUEST
        rows = [{key: str(value) if value is not None else '' for key, value in row.items()} for row in result.rows]
        return Response({'rows': rows, 'errors': result.errors, 'imported': result.imported, 'is_valid': result.is_valid}, status=code)

    @action(detail=False, methods=['post'], url_path='preview-csv')
    def preview_csv(self, request): return self._import_response(request, False)
    @action(detail=False, methods=['post'], url_path='import-csv')
    def import_csv(self, request): return self._import_response(request, True)


class EventCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = EventCategory.objects.all(); serializer_class = EventCategoryManagementSerializer
class AcademyEventManagementViewSet(SafeDestroyModelViewSet):
    queryset = AcademyEvent.objects.select_related('category').all(); serializer_class = AcademyEventManagementSerializer
class MentorProfileManagementViewSet(SafeDestroyModelViewSet):
    queryset = MentorProfile.objects.select_related('user').all(); serializer_class = MentorProfileManagementSerializer
class ForumCategoryManagementViewSet(SafeDestroyModelViewSet):
    queryset = ForumCategory.objects.all(); serializer_class = ForumCategoryManagementSerializer
class ForumPostManagementViewSet(SafeDestroyModelViewSet):
    queryset = ForumPost.objects.select_related('author', 'category').all(); serializer_class = ForumPostModerationSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']
