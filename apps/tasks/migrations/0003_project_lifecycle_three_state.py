import django.utils.timezone
from django.db import migrations, models


CANONICAL_COLUMNS = (
    ('To Do', 0, {'backlog', 'to do'}),
    ('In Progress', 1, {'in progress', 'blocked'}),
    ('Completed', 2, {'done', 'completed'}),
)


def canonicalize_columns(apps, schema_editor):
    Board = apps.get_model('tasks', 'Board')
    BoardColumn = apps.get_model('tasks', 'BoardColumn')
    Task = apps.get_model('tasks', 'Task')

    for board in Board.objects.all().iterator():
        original_columns = list(board.columns.order_by('position', 'id'))
        next_position = max((column.position for column in original_columns), default=-1) + 10
        destinations = {}
        for index, (name, _position, _aliases) in enumerate(CANONICAL_COLUMNS):
            destinations[name] = BoardColumn.objects.create(
                board=board,
                name=f'__canonical_{index}_{board.pk}__',
                position=next_position + index,
            )

        grouped_tasks = {name: [] for name, _position, _aliases in CANONICAL_COLUMNS}
        for column in original_columns:
            normalized = column.name.strip().lower()
            destination_name = 'In Progress'
            for name, _position, aliases in CANONICAL_COLUMNS:
                if normalized in aliases:
                    destination_name = name
                    break
            grouped_tasks[destination_name].extend(
                Task.objects.filter(column=column).order_by('position', 'id')
            )

        for name, tasks in grouped_tasks.items():
            destination = destinations[name]
            for position, task in enumerate(tasks):
                Task.objects.filter(pk=task.pk).update(column=destination, position=position)

        BoardColumn.objects.filter(pk__in=[column.pk for column in original_columns]).delete()
        for name, position, _aliases in CANONICAL_COLUMNS:
            destination = destinations[name]
            destination.name = name
            destination.position = position
            destination.save(update_fields=['name', 'position'])


class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0002_project_projectnotification_task_parent_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='start_date',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
        migrations.AddField(
            model_name='project',
            name='status',
            field=models.CharField(
                choices=[
                    ('planning', 'Planning'),
                    ('active', 'Active'),
                    ('on_hold', 'On Hold'),
                    ('completed', 'Completed'),
                ],
                default='planning',
                max_length=12,
            ),
        ),
        migrations.RunPython(canonicalize_columns, migrations.RunPython.noop),
    ]
