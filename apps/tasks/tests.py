from pathlib import Path

from django.contrib.staticfiles import finders
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

    def test_task_positions_remain_contiguous_after_drag_style_moves(self):
        board = self.client.post('/api/v1/task-boards/', {'name': 'Ordered Board'}, format='json').data
        backlog, todo = list(BoardColumn.objects.filter(board_id=board['id'])[:2])
        task_ids = []
        for title in ['First', 'Second', 'Third']:
            created = self.client.post('/api/v1/tasks/', {
                'board': board['id'], 'column': backlog.id, 'title': title,
            }, format='json')
            self.assertEqual(created.status_code, status.HTTP_201_CREATED)
            task_ids.append(created.data['id'])

        self.assertEqual(
            list(Task.objects.filter(column=backlog).values_list('position', flat=True)),
            [0, 1, 2],
        )
        reordered = self.client.post(
            f'/api/v1/tasks/{task_ids[2]}/move/', {'column': backlog.id, 'position': 0}, format='json'
        )
        self.assertEqual(reordered.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(Task.objects.filter(column=backlog).values_list('title', 'position')),
            [('Third', 0), ('First', 1), ('Second', 2)],
        )

        moved = self.client.post(
            f'/api/v1/tasks/{task_ids[0]}/move/', {'column': todo.id, 'position': 0}, format='json'
        )
        self.assertEqual(moved.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(Task.objects.filter(column=backlog).values_list('title', 'position')),
            [('Third', 0), ('Second', 1)],
        )
        self.assertEqual(
            list(Task.objects.filter(column=todo).values_list('title', 'position')),
            [('First', 0)],
        )

    def test_user_cannot_add_task_to_another_users_board(self):
        other = User.objects.create_user(username='board-owner', password='test-pass-123')
        self.client.force_authenticate(other)
        board = self.client.post('/api/task-boards/', {'name': 'Owned Elsewhere'}, format='json').data
        column = BoardColumn.objects.filter(board_id=board['id']).first()
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/tasks/', {'board': board['id'], 'column': column.id, 'title': 'Intrusion'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_kanban_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Tasks &amp; Kanban')

    def test_kanban_supports_drag_and_arrow_controls(self):
        source = Path(finders.find('js/modules/tasks/kanban.js')).read_text(encoding='utf-8')
        self.assertIn("addEventListener('dragstart'", source)
        self.assertIn("addEventListener('pointerdown'", source)
        self.assertIn('data-drag-handle', source)
        self.assertIn('data-move-direction', source)
        self.assertIn("await moveTask(taskId, columnId, position)", source)
