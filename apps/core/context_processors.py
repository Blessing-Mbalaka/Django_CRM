from functionalities.crm_core.navigation import get_suite_navigation


def suite_navigation(request):
    if not request.user.is_authenticated:
        return {'suite_navigation': [], 'project_notifications': [], 'project_notification_count': 0}

    from apps.tasks.models import ProjectNotification
    notifications = ProjectNotification.objects.filter(recipient=request.user).select_related('project')[:8]
    return {
        'suite_navigation': get_suite_navigation(request.user),
        'project_notifications': notifications,
        'project_notification_count': ProjectNotification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count(),
    }
