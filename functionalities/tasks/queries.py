from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.tasks.models import Board, Project, Task


def accessible_boards(user):
    return Board.objects.filter(
        models.Q(owner=user)
        | models.Q(projects__assignees=user)
        | models.Q(tasks__assignee=user)
    ).distinct()


def accessible_tasks(user):
    return Task.objects.filter(
        models.Q(board__owner=user)
        | models.Q(assignee=user)
        | models.Q(project_card_for__assignees=user)
        | models.Q(parent_task__project_card_for__assignees=user)
    ).distinct()


def workspace_tasks(user):
    return accessible_tasks(user).filter(project_card_for__isnull=True)


def accessible_projects(user):
    return Project.objects.filter(
        models.Q(board__owner=user) | models.Q(assignees=user)
    ).distinct()


def dashboard_summary(user):
    today = timezone.localdate()
    tasks = list(workspace_tasks(user).select_related('column'))
    projects = list(accessible_projects(user))
    unfinished = [task for task in tasks if task.column.name != 'Completed']
    return {
        'active_projects': sum(project.status == Project.Status.ACTIVE for project in projects),
        'due_today': sum(task.due_date == today for task in unfinished),
        'completed': sum(task.column.name == 'Completed' for task in tasks),
        'overdue': sum(bool(task.due_date and task.due_date < today) for task in unfinished),
        'total_tasks': len(tasks),
        'status_counts': {
            'to_do': sum(task.column.name == 'To Do' for task in tasks),
            'in_progress': sum(task.column.name == 'In Progress' for task in tasks),
            'completed': sum(task.column.name == 'Completed' for task in tasks),
            'overdue': sum(bool(task.due_date and task.due_date < today) for task in unfinished),
        },
    }


def calendar_items(user, start, end):
    tasks = workspace_tasks(user).filter(due_date__range=(start, end)).select_related('column')
    projects = accessible_projects(user).filter(due_date__range=(start, end))
    return {
        'tasks': [
            {
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date.isoformat(),
                'status': task.column.name,
                'overdue': task.column.name != 'Completed' and task.due_date < timezone.localdate(),
            }
            for task in tasks.order_by('due_date', 'id')
        ],
        'projects': [
            {
                'id': project.id,
                'name': project.name,
                'due_date': project.due_date.isoformat(),
                'status': project.status,
            }
            for project in projects.order_by('due_date', 'id')
        ],
    }


def team_summary(user):
    today = timezone.localdate()
    tasks = list(workspace_tasks(user).select_related('assignee', 'column', 'board__owner'))
    projects = accessible_projects(user).prefetch_related('assignees')
    user_ids = {user.id}
    user_ids.update(task.assignee_id for task in tasks if task.assignee_id)
    user_ids.update(task.board.owner_id for task in tasks)
    for project in projects:
        user_ids.add(project.created_by_id)
        user_ids.update(project.assignees.values_list('id', flat=True))

    people = get_user_model().objects.filter(id__in=user_ids, is_active=True).order_by('last_name', 'first_name', 'id')
    result = []
    for person in people:
        assigned = [task for task in tasks if task.assignee_id == person.id]
        active = [task for task in assigned if task.column.name != 'Completed']
        result.append({
            'id': person.id,
            'name': person.get_full_name() or person.username,
            'role': person.get_role_display(),
            'initials': person.initials or (person.username[:2].upper()),
            'active_tasks': len(active),
            'completed_tasks': sum(task.column.name == 'Completed' for task in assigned),
            'due_today': sum(task.due_date == today for task in active),
        })
    return result
