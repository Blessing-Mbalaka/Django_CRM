from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from pathlib import Path

from functionalities.tasks.queries import accessible_tasks
from .models import ProjectNotification, TaskAttachment


@login_required
def board_view(request):
    people = [
        {
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'role': user.get_role_display(),
        }
        for user in get_user_model().objects.filter(is_active=True).order_by('last_name', 'first_name', 'id')
    ]
    config = {
        'user': {
            'id': request.user.id,
            'name': request.user.get_full_name() or request.user.username,
            'role': request.user.get_role_display(),
        },
        'people': people,
        'urls': {
            'boards': reverse('task-board-list'),
            'tasks': reverse('task-list'),
            'projects': reverse('project-list'),
            'dashboard': reverse('task-dashboard'),
            'calendar': reverse('task-calendar'),
            'team': reverse('task-team'),
            'attachments': reverse('task-attachment-list'),
        },
    }
    return render(request, 'tasks/board.html', {'task_workspace_config': config})


@login_required
def open_project_notification(request, pk):
    notification = get_object_or_404(
        ProjectNotification.objects.select_related('project'),
        pk=pk,
        recipient=request.user,
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return redirect(f'/tasks/?board={notification.project.board_id}&project={notification.project_id}')


@login_required
def download_attachment(request, pk):
    attachment = get_object_or_404(
        TaskAttachment.objects.filter(task__in=accessible_tasks(request.user)),
        pk=pk,
    )
    return FileResponse(
        attachment.file.open('rb'),
        as_attachment=True,
        filename=Path(attachment.original_name).name,
        content_type=attachment.mime_type or 'application/octet-stream',
    )
