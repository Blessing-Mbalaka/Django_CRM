from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from .models import Board, BoardColumn, Project, ProjectNotification, Task, TaskActivity, TaskComment


class BoardColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardColumn
        fields = ['id', 'board', 'name', 'position']
        read_only_fields = ['id']

    def validate_board(self, board):
        if board.owner_id != self.context['request'].user.id:
            raise serializers.ValidationError('You do not have access to this board.')
        return board


class BoardSerializer(serializers.ModelSerializer):
    columns = BoardColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'owner', 'columns', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source='assignee.get_full_name', read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'board', 'column', 'column_name', 'title', 'description', 'priority', 'position', 'creator', 'assignee', 'assignee_name', 'client', 'engagement', 'due_date', 'completed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'position', 'creator', 'completed_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        board = attrs.get('board', getattr(self.instance, 'board', None))
        column = attrs.get('column', getattr(self.instance, 'column', None))
        request = self.context.get('request')
        if request and board and board.owner_id != request.user.id:
            raise serializers.ValidationError({'board': 'You do not have access to this board.'})
        if board and column and column.board_id != board.id:
            raise serializers.ValidationError({'column': 'Column must belong to the selected board.'})
        return attrs

    def create(self, validated_data):
        column = validated_data['column']
        last_position = Task.objects.filter(column=column).aggregate(value=Max('position'))['value']
        validated_data['position'] = (last_position + 1) if last_position is not None else 0
        return super().create(validated_data)


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'author', 'author_name', 'body', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

    def validate_task(self, task):
        if task.board.owner_id != self.context['request'].user.id:
            raise serializers.ValidationError('You do not have access to this task.')
        return task


class TaskActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskActivity
        fields = ['id', 'task', 'actor', 'action', 'detail', 'created_at']
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    assignees = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=get_user_model().objects.filter(is_active=True),
    )
    assignee_details = serializers.SerializerMethodField()
    subtasks = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    subtask_details = serializers.SerializerMethodField()
    column = serializers.IntegerField(source='kanban_task.column_id', read_only=True)
    column_name = serializers.CharField(source='kanban_task.column.name', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'board', 'name', 'description', 'assignees', 'assignee_details',
            'due_date', 'kanban_task', 'column', 'column_name', 'subtasks',
            'subtask_details', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'kanban_task', 'created_at', 'updated_at']

    def validate_board(self, board):
        if board.owner_id != self.context['request'].user.id:
            raise serializers.ValidationError('Only the board owner can create projects on this board.')
        return board

    def validate_assignees(self, assignees):
        if not assignees:
            raise serializers.ValidationError('Assign the project to at least one employee.')
        return assignees

    @transaction.atomic
    def create(self, validated_data):
        assignees = validated_data.pop('assignees')
        subtask_titles = validated_data.pop('subtasks', [])
        board = validated_data['board']
        creator = self.context['request'].user
        project = Project.objects.create(created_by=creator, **validated_data)
        project.assignees.set(assignees)

        first_column = board.columns.order_by('position', 'id').first()
        if not first_column:
            raise serializers.ValidationError({'board': 'The board needs at least one column.'})
        last_position = Task.objects.filter(column=first_column, parent_task__isnull=True).aggregate(value=Max('position'))['value']
        project_task = Task.objects.create(
            board=board,
            column=first_column,
            title=project.name,
            description=project.description,
            priority=Task.Priority.MEDIUM,
            position=(last_position + 1) if last_position is not None else 0,
            creator=creator,
            assignee=assignees[0],
            due_date=project.due_date,
        )
        project.kanban_task = project_task
        project.save(update_fields=['kanban_task', 'updated_at'])

        unique_titles = list(dict.fromkeys(title.strip() for title in subtask_titles if title.strip()))
        Task.objects.bulk_create([
            Task(
                board=board,
                column=first_column,
                parent_task=project_task,
                title=title,
                priority=Task.Priority.MEDIUM,
                position=index,
                creator=creator,
                assignee=assignees[0],
                due_date=project.due_date,
            )
            for index, title in enumerate(unique_titles)
        ])
        ProjectNotification.objects.bulk_create([
            ProjectNotification(
                recipient=user,
                project=project,
                message=f'You were assigned to “{project.name}”. Open its shared Kanban board.',
            )
            for user in assignees
        ])
        return project

    def get_assignee_details(self, obj):
        return [
            {'id': user.id, 'name': user.get_full_name() or user.username}
            for user in obj.assignees.all()
        ]

    def get_subtask_details(self, obj):
        if not obj.kanban_task_id:
            return []
        return [
            {
                'id': task.id,
                'title': task.title,
                'column': task.column_id,
                'column_name': task.column.name,
            }
            for task in obj.kanban_task.subtasks.all()
        ]
