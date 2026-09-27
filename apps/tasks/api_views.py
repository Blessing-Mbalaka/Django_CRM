from django.db import models
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from functionalities.tasks.services import move_task
from .models import Board, BoardColumn, Project, Task, TaskActivity, TaskComment
from .serializers import BoardColumnSerializer, BoardSerializer, ProjectSerializer, TaskActivitySerializer, TaskCommentSerializer, TaskSerializer


class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Board.objects.filter(
            models.Q(owner=self.request.user) |
            models.Q(projects__assignees=self.request.user) |
            models.Q(tasks__assignee=self.request.user)
        ).distinct()
        if self.action not in ['list', 'retrieve']:
            qs = qs.filter(owner=self.request.user)
        return qs.prefetch_related('columns')

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        BoardColumn.objects.bulk_create([
            BoardColumn(board=board, name='To Do', position=0),
            BoardColumn(board=board, name='In Progress', position=1),
            BoardColumn(board=board, name='Completed', position=2),
        ])


class BoardColumnViewSet(viewsets.ModelViewSet):
    serializer_class = BoardColumnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = BoardColumn.objects.filter(
            models.Q(board__owner=self.request.user) |
            models.Q(board__projects__assignees=self.request.user) |
            models.Q(board__tasks__assignee=self.request.user)
        ).distinct()
        if self.action not in ['list', 'retrieve']:
            qs = qs.filter(board__owner=self.request.user)
        return qs.select_related('board')

    def perform_destroy(self, instance):
        if instance.tasks.exists():
            raise serializers.ValidationError('Move or delete this column’s tasks before deleting the column.')
        instance.delete()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.filter(
            models.Q(board__owner=self.request.user) |
            models.Q(assignee=self.request.user) |
            models.Q(project_card_for__assignees=self.request.user)
        ).filter(parent_task__isnull=True).distinct().select_related('board', 'column', 'creator', 'assignee', 'client', 'engagement')
        if self.action in ['update', 'partial_update', 'destroy']:
            qs = qs.filter(board__owner=self.request.user)
        if board := self.request.query_params.get('board'):
            qs = qs.filter(board_id=board)
        if assignee := self.request.query_params.get('assignee'):
            qs = qs.filter(assignee_id=assignee)
        return qs

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        task = self.get_object()
        try:
            destination = BoardColumn.objects.get(pk=request.data.get('column'), board=task.board)
            position = int(request.data.get('position', 0))
        except (BoardColumn.DoesNotExist, TypeError, ValueError):
            raise serializers.ValidationError({'column': 'A valid destination column and position are required.'})
        task = move_task(task=task, destination=destination, position=position, actor=request.user)
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskComment.objects.filter(
            models.Q(task__board__owner=self.request.user) |
            models.Q(task__assignee=self.request.user) |
            models.Q(task__project_card_for__assignees=self.request.user)
        ).distinct().select_related('task', 'author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskActivity.objects.filter(
            models.Q(task__board__owner=self.request.user) |
            models.Q(task__assignee=self.request.user) |
            models.Q(task__project_card_for__assignees=self.request.user)
        ).distinct().select_related('task', 'actor')


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = Project.objects.filter(
            models.Q(board__owner=self.request.user) |
            models.Q(assignees=self.request.user)
        ).distinct().select_related('board', 'kanban_task__column').prefetch_related(
            'assignees', 'kanban_task__subtasks__column'
        )
        if board := self.request.query_params.get('board'):
            qs = qs.filter(board_id=board)
        return qs
