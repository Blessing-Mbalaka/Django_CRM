from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from functionalities.tasks.services import move_task
from .models import Board, BoardColumn, Task, TaskActivity, TaskComment
from .serializers import BoardColumnSerializer, BoardSerializer, TaskActivitySerializer, TaskCommentSerializer, TaskSerializer


class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user).prefetch_related('columns')

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        BoardColumn.objects.bulk_create([
            BoardColumn(board=board, name='Backlog', position=0),
            BoardColumn(board=board, name='To Do', position=1),
            BoardColumn(board=board, name='In Progress', position=2),
            BoardColumn(board=board, name='Blocked', position=3),
            BoardColumn(board=board, name='Done', position=4),
        ])


class BoardColumnViewSet(viewsets.ModelViewSet):
    serializer_class = BoardColumnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BoardColumn.objects.filter(board__owner=self.request.user).select_related('board')

    def perform_destroy(self, instance):
        if instance.tasks.exists():
            raise serializers.ValidationError('Move or delete this column’s tasks before deleting the column.')
        instance.delete()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.filter(board__owner=self.request.user).select_related('board', 'column', 'creator', 'assignee', 'client', 'engagement')
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
        return TaskComment.objects.filter(task__board__owner=self.request.user).select_related('task', 'author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskActivity.objects.filter(task__board__owner=self.request.user).select_related('task', 'actor')
