from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Certificate, Course, CourseModule, ForumPost, LearningPath
from .permissions import is_academy_manager
from functionalities.crm_core.navigation import get_suite_navigation


def _api_v1(name):
    """Prefer the canonical versioned mount when URL names also exist under /api/."""
    return reverse(name).replace('/api/', '/api/v1/', 1)


@login_required
def academy_index(request):
    academy_tools = []
    for group in get_suite_navigation(request.user):
        if group['key'] == 'developer':
            continue
        for item in group['catalogue_items']:
            academy_tools.append({
                'label': item['label'],
                'description': item['description'],
                'url': item['url'],
                'svg_path': item['svg_path'],
                'group': group['label'],
                'coming_soon': item.get('coming_soon', False),
            })
    can_manage = is_academy_manager(request.user)
    management_data = None
    if can_manage:
        management_names = {
            'courseCategories': 'academy-manage-course-category-list',
            'courseLevels': 'academy-manage-course-level-list', 'paths': 'academy-manage-path-list',
            'courses': 'academy-manage-course-list', 'modules': 'academy-manage-module-list',
            'resourceCategories': 'academy-manage-resource-category-list', 'resources': 'academy-manage-resource-list',
            'diagnosticCategories': 'academy-manage-diagnostic-category-list', 'diagnostics': 'academy-manage-diagnostic-list',
            'diagnosticQuestions': 'academy-manage-diagnostic-question-list', 'diagnosticOptions': 'academy-manage-diagnostic-option-list',
            'diagnosticRecommendations': 'academy-manage-diagnostic-recommendation-list',
            'opportunityCategories': 'academy-manage-opportunity-category-list', 'funding': 'academy-manage-funding-list',
            'eventCategories': 'academy-manage-event-category-list', 'events': 'academy-manage-event-list',
            'mentors': 'academy-manage-mentor-list', 'forumCategories': 'academy-manage-forum-category-list',
            'forumPosts': 'academy-manage-forum-post-list',
        }
        management_data = {
            'can_manage': True,
            'endpoints': {key: _api_v1(name) for key, name in management_names.items()},
            'choices': {
                'businessStages': list(LearningPath.BusinessStage.choices),
                'courseLevels': list(Course.Level.choices),
                'moduleTypes': list(CourseModule.Type.choices),
                'forumStatuses': list(ForumPost.Status.choices),
            },
        }
    response = render(request, 'academy/index.html', {
        'academy_paths_url': _api_v1('academy-path-list'),
        'academy_courses_url': _api_v1('academy-course-list'),
        'academy_enrollments_url': _api_v1('academy-enrollment-list'),
        'academy_resources_url': _api_v1('academy-resource-list'),
        'academy_diagnostics_url': _api_v1('academy-diagnostic-list'),
        'academy_funding_url': _api_v1('academy-funding-list'),
        'academy_events_url': _api_v1('academy-event-list'),
        'academy_mentors_url': _api_v1('academy-mentor-list'),
        'academy_bookings_url': _api_v1('academy-mentorship-booking-list'),
        'academy_conversations_url': _api_v1('academy-conversation-list'),
        'academy_messages_url': _api_v1('academy-message-list'),
        'academy_forum_categories_url': _api_v1('academy-forum-category-list'),
        'academy_forum_posts_url': _api_v1('academy-forum-post-list'),
        'academy_forum_replies_url': _api_v1('academy-forum-reply-list'),
        'academy_tools': academy_tools,
        'can_manage_academy': can_manage,
        'academy_management_data': management_data,
    })
    response.headers['Content-Security-Policy'] = (
        'frame-src https://www.youtube.com https://www.youtube-nocookie.com'
    )
    return response


@login_required
def certificate_detail(request, verification_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related('enrollment__user'),
        verification_id=verification_id,
        enrollment__user=request.user,
    )
    return render(request, 'academy/certificate.html', {'certificate': certificate})
