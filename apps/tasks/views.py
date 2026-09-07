from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render

from .models import ProjectNotification


@login_required
def board_view(request):
    assignees = get_user_model().objects.filter(is_active=True).exclude(pk=request.user.pk)
    return render(request, 'tasks/board.html', {'assignees': assignees})


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
