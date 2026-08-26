from django.core.exceptions import ValidationError


def validate_task_column(*, board, column):
    if column.board_id != board.id:
        raise ValidationError('Column must belong to the task board.')

