from django.db import transaction

from apps.tasks.models import Task, TaskActivity
from .validators import validate_task_column


@transaction.atomic
def move_task(*, task, destination, position, actor):
    validate_task_column(board=task.board, column=destination)
    position = max(0, int(position))
    old_column_id = task.column_id
    old_position = task.position

    Task.objects.filter(column=destination, position__gte=position).exclude(pk=task.pk).update(position=models.F('position') + 1)
    task.column = destination
    task.position = position
    task.save(update_fields=['column', 'position', 'updated_at'])
    TaskActivity.objects.create(
        task=task,
        actor=actor,
        action='moved',
        detail={'from_column': old_column_id, 'from_position': old_position, 'to_column': destination.id, 'to_position': position},
    )
    return task


from django.db import models  # Kept below domain imports to make F-expression intent explicit.

