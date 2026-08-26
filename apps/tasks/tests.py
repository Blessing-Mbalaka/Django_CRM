from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import BoardColumn, Task


class TaskApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tasks', password='test-pass-123')
        self.client.force_authenticate(self.user)

    def test_board_creates_default_columns_and_task_move_persists(self):
        board_response = self.client.post('/api/task-boards/', {'name': 'Operations'}, format='json')
        self.assertEqual(board_response.status_code, status.HTTP_201_CREATED)
        board_id = board_response.data['id']
        columns = BoardColumn.objects.filter(board_id=board_id)
        self.assertEqual(columns.count(), 5)
        backlog = columns.get(name='Backlog')
        done = columns.get(name='Done')
        task_response = self.client.post('/api/tasks/', {'board': board_id, 'column': backlog.id, 'title': 'Send invoice'}, format='json')
        self.assertEqual(task_response.status_code, status.HTTP_201_CREATED)
        move = self.client.post(f"/api/tasks/{task_response.data['id']}/move/", {'column': done.id, 'position': 0}, format='json')
        self.assertEqual(move.status_code, status.HTTP_200_OK)
        task = Task.objects.get(pk=task_response.data['id'])
        self.assertEqual(task.column, done)
        self.assertEqual(task.activities.filter(action='moved').count(), 1)

    def test_user_cannot_read_another_users_board(self):
        other = User.objects.create_user(username='other-tasks', password='test-pass-123')
        self.client.force_authenticate(other)
        self.client.post('/api/task-boards/', {'name': 'Private Board'}, format='json')
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/task-boards/')
        self.assertEqual(response.data['count'], 0)

    def test_user_cannot_add_task_to_another_users_board(self):
        other = User.objects.create_user(username='board-owner', password='test-pass-123')
        self.client.force_authenticate(other)
        board = self.client.post('/api/task-boards/', {'name': 'Owned Elsewhere'}, format='json').data
        column = BoardColumn.objects.filter(board_id=board['id']).first()
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/tasks/', {'board': board['id'], 'column': column.id, 'title': 'Intrusion'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
