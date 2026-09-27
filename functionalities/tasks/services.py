from django.db import transaction
from django.utils import timezone

from apps.tasks.models import Task, TaskActivity
from .validators import validate_task_column


@transaction.atomic
def move_task(*, task, destination, position, actor):
    validate_task_column(board=task.board, column=destination)
    position = max(0, int(position))
    old_column_id = task.column_id
    old_position = task.position

    # Lock both affected columns and rewrite contiguous positions. This handles
    # cross-column moves and reordering inside the same column consistently.
    affected_column_ids = {old_column_id, destination.id}
    locked_tasks = list(
        Task.objects.select_for_update()
        .filter(column_id__in=affected_column_ids)
        .filter(parent_task_id=task.parent_task_id)
        .order_by('position', 'id')
    )
    source_tasks = [item for item in locked_tasks if item.column_id == old_column_id and item.pk != task.pk]
    if old_column_id == destination.id:
        destination_tasks = source_tasks
    else:
        destination_tasks = [item for item in locked_tasks if item.column_id == destination.id and item.pk != task.pk]

    position = min(position, len(destination_tasks))
    destination_tasks.insert(position, task)

    if old_column_id != destination.id:
        for index, sibling in enumerate(source_tasks):
            if sibling.position != index:
                Task.objects.filter(pk=sibling.pk).update(position=index)
    for index, sibling in enumerate(destination_tasks):
        if sibling.pk != task.pk and sibling.position != index:
            Task.objects.filter(pk=sibling.pk).update(position=index)

    task.column = destination
    task.position = position
    task.completed_at = timezone.now() if destination.name == 'Completed' else None
    task.save(update_fields=['column', 'position', 'completed_at', 'updated_at'])
    TaskActivity.objects.create(
        task=task,
        actor=actor,
        action='moved',
        detail={'from_column': old_column_id, 'from_position': old_position, 'to_column': destination.id, 'to_position': position},
    )
    return task
