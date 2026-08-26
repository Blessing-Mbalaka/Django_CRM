from rest_framework import serializers

from .models import Board, BoardColumn, Task, TaskActivity, TaskComment


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
        read_only_fields = ['id', 'creator', 'completed_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        board = attrs.get('board', getattr(self.instance, 'board', None))
        column = attrs.get('column', getattr(self.instance, 'column', None))
        request = self.context.get('request')
        if request and board and board.owner_id != request.user.id:
            raise serializers.ValidationError({'board': 'You do not have access to this board.'})
        if board and column and column.board_id != board.id:
            raise serializers.ValidationError({'column': 'Column must belong to the selected board.'})
        return attrs


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
