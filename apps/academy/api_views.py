from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch, Q
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import (
    AcademyEvent, AcademyResource, AcademyResourceCategory, ChatMessage,
    Conversation, Course, CourseCategory, CourseEnrollment, CourseLevel,
    CourseModule, Diagnostic, DiagnosticCategory, EventCategory, ForumCategory,
    DiagnosticOption, DiagnosticQuestion, ForumPost, ForumReply, FundingOpportunity, LearningPath, MentorProfile,
    MentorshipBooking, OpportunityCategory,
)
from .serializers import (
    AcademyEventSerializer, AcademyResourceSerializer, ChatMessageSerializer,
    ConversationSerializer, CourseCategorySerializer, CourseDetailSerializer,
    CourseEnrollmentSerializer, CourseLevelSerializer, CourseListSerializer,
    DiagnosticCategorySerializer, DiagnosticSerializer,
    DiagnosticSubmissionSerializer, EventCategorySerializer,
    EventRegistrationSerializer, ForumCategorySerializer, ForumPostSerializer,
    ForumReplySerializer, FundingOpportunitySerializer,
    LearningPathSummarySerializer, MentorProfileSerializer,
    MentorshipBookingSerializer, OpportunityCategorySerializer,
    ResourceCategorySerializer,
)
from .services import complete_module, score_diagnostic, submit_quiz


class ActiveCategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None


class CourseCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = CourseCategorySerializer
    queryset = CourseCategory.objects.filter(is_active=True)


class CourseLevelViewSet(ActiveCategoryViewSet):
    serializer_class = CourseLevelSerializer
    queryset = CourseLevel.objects.filter(is_active=True)


class ResourceCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = ResourceCategorySerializer
    queryset = AcademyResourceCategory.objects.filter(is_active=True)


class DiagnosticCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = DiagnosticCategorySerializer
    queryset = DiagnosticCategory.objects.filter(is_active=True)


class OpportunityCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = OpportunityCategorySerializer
    queryset = OpportunityCategory.objects.filter(is_active=True)


class EventCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = EventCategorySerializer
    queryset = EventCategory.objects.filter(is_active=True)


class ForumCategoryViewSet(ActiveCategoryViewSet):
    serializer_class = ForumCategorySerializer
    queryset = ForumCategory.objects.filter(is_active=True)


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
        user_enrollments = CourseEnrollment.objects.filter(user=self.request.user)
        queryset = Course.objects.filter(
            is_published=True,
            path__is_published=True,
        ).select_related('path', 'category', 'level_config').prefetch_related(
            Prefetch('modules', queryset=published_modules, to_attr='published_modules'),
            Prefetch('enrollments', queryset=user_enrollments, to_attr='current_user_enrollments'),
        )
        if path_slug := self.request.query_params.get('path'):
            queryset = queryset.filter(path__slug=path_slug)
        if category_slug := self.request.query_params.get('category'):
            queryset = queryset.filter(category__slug=category_slug)
        if level_slug := self.request.query_params.get('level'):
            queryset = queryset.filter(Q(level_config__slug=level_slug) | Q(level=level_slug))
        return queryset

    @action(detail=True, methods=['post'])
    def enrol(self, request, slug=None):
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user, course=self.get_object()
        )
        return Response(
            CourseEnrollmentSerializer(enrollment, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CourseEnrollmentViewSet(ReadOnlyModelViewSet):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CourseEnrollment.objects.filter(user=self.request.user).select_related(
            'course', 'course__path', 'course__category', 'course__level_config'
        )

    def _module(self, request, enrollment):
        try:
            return enrollment.course.modules.get(pk=request.data.get('module'), is_published=True)
        except (CourseModule.DoesNotExist, ValueError, TypeError) as exc:
            raise serializers.ValidationError({'module': 'Choose a published module from this course.'}) from exc

    @action(detail=True, methods=['post'], url_path='complete-module')
    def complete_module_action(self, request, pk=None):
        enrollment = self.get_object()
        try:
            complete_module(enrollment, self._module(request, enrollment), request.data.get('response', ''))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        enrollment.refresh_from_db()
        return Response(self.get_serializer(enrollment).data)

    @action(detail=True, methods=['post'], url_path='submit-quiz')
    def submit_quiz_action(self, request, pk=None):
        enrollment = self.get_object()
        try:
            selected = int(request.data.get('selected_option'))
            attempt = submit_quiz(enrollment, self._module(request, enrollment), selected)
        except (TypeError, ValueError):
            raise serializers.ValidationError({'selected_option': 'Choose a valid option number.'})
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        enrollment.refresh_from_db()
        return Response({'is_correct': attempt.is_correct, 'enrollment': self.get_serializer(enrollment).data})


class AcademyResourceViewSet(ReadOnlyModelViewSet):
    serializer_class = AcademyResourceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = AcademyResource.objects.filter(is_published=True).select_related('category')
        if category := self.request.query_params.get('category'):
            queryset = queryset.filter(category__slug=category)
        return queryset.order_by('-created_at')


class DiagnosticViewSet(ReadOnlyModelViewSet):
    serializer_class = DiagnosticSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        active_options = DiagnosticOption.objects.filter(is_active=True).order_by('position', 'id')
        active_questions = DiagnosticQuestion.objects.filter(is_active=True).select_related(
            'category'
        ).prefetch_related(Prefetch('options', queryset=active_options))
        return Diagnostic.objects.filter(is_published=True).prefetch_related(
            Prefetch('questions', queryset=active_questions)
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, slug=None):
        try:
            submission = score_diagnostic(request.user, self.get_object(), request.data.get('answers', {}))
        except (DjangoValidationError, TypeError, ValueError) as exc:
            detail = exc.messages if isinstance(exc, DjangoValidationError) else str(exc)
            raise serializers.ValidationError(detail) from exc
        output = DiagnosticSubmissionSerializer(submission)
        return Response(output.data, status=status.HTTP_201_CREATED)


class FundingOpportunityViewSet(ReadOnlyModelViewSet):
    serializer_class = FundingOpportunitySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = FundingOpportunity.objects.filter(is_published=True).select_related('category')
        if category := self.request.query_params.get('category'):
            queryset = queryset.filter(category__slug=category)
        return queryset.order_by('closes_on', 'title')


class AcademyEventViewSet(ReadOnlyModelViewSet):
    serializer_class = AcademyEventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = AcademyEvent.objects.filter(is_published=True).select_related('category')
        if category := self.request.query_params.get('category'):
            queryset = queryset.filter(category__slug=category)
        return queryset.order_by('starts_at')

    @action(detail=True, methods=['post'])
    def register(self, request, slug=None):
        event = self.get_object()
        if event.capacity and event.registrations.count() >= event.capacity:
            raise serializers.ValidationError('This event is full.')
        registration, created = event.registrations.get_or_create(user=request.user)
        return Response(
            EventRegistrationSerializer(registration).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MentorProfileViewSet(ReadOnlyModelViewSet):
    serializer_class = MentorProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = MentorProfile.objects.filter(is_active=True).select_related('user')


class MentorshipBookingViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MentorshipBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MentorshipBooking.objects.filter(
            Q(learner=self.request.user) | Q(mentor__user=self.request.user)
        ).select_related('learner', 'mentor__user').distinct()

    def perform_create(self, serializer):
        serializer.save(learner=self.request.user)

    def _respond(self, request, booking, new_status):
        if booking.mentor.user_id != request.user.id:
            raise PermissionDenied('Only the selected mentor can respond to this request.')
        if booking.status != booking.Status.REQUESTED:
            raise serializers.ValidationError('This request has already been answered.')
        booking.status = new_status
        booking.save(update_fields=['status'])
        if new_status == booking.Status.ACCEPTED:
            Conversation.objects.get_or_create(booking=booking)
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        return self._respond(request, self.get_object(), MentorshipBooking.Status.ACCEPTED)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        return self._respond(request, self.get_object(), MentorshipBooking.Status.DECLINED)


class ConversationViewSet(ReadOnlyModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            Q(booking__learner=self.request.user) | Q(booking__mentor__user=self.request.user)
        ).select_related('booking', 'booking__mentor__user').prefetch_related('messages__sender').distinct()


class ChatMessageViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ChatMessage.objects.filter(
            Q(conversation__booking__learner=self.request.user) |
            Q(conversation__booking__mentor__user=self.request.user)
        ).select_related('sender', 'conversation').distinct()
        if conversation := self.request.query_params.get('conversation'):
            queryset = queryset.filter(conversation_id=conversation)
        return queryset

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        if not conversation.has_participant(self.request.user):
            raise serializers.ValidationError('You are not a participant in this conversation.')
        serializer.save(sender=self.request.user)


class ForumPostViewSet(viewsets.ModelViewSet):
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = ForumPost.objects.filter(status=ForumPost.Status.PUBLISHED).select_related(
            'author', 'category'
        ).prefetch_related('replies__author')
        if category := self.request.query_params.get('category'):
            queryset = queryset.filter(category__slug=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author_id != self.request.user.id:
            raise serializers.ValidationError('Only the author can edit this post.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise serializers.ValidationError('Only the author can delete this post.')
        instance.delete()


class ForumReplyViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ForumReplySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ForumReply.objects.filter(
            is_hidden=False, post__status=ForumPost.Status.PUBLISHED
        ).select_related('author', 'post')
        if post := self.request.query_params.get('post'):
            queryset = queryset.filter(post_id=post)
        return queryset

    def perform_create(self, serializer):
        if serializer.validated_data['post'].is_locked:
            raise serializers.ValidationError('This discussion is locked.')
        serializer.save(author=self.request.user)
