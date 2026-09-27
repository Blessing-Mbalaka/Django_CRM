from django.db import models

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
    ).filter(parent_task__isnull=True).distinct()


def accessible_projects(user):
    return Project.objects.filter(
        models.Q(board__owner=user) | models.Q(assignees=user)
    ).distinct()
