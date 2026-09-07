from pathlib import Path

from django.contrib.staticfiles import finders
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import BoardColumn, Project, ProjectNotification, Task


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


class SharedProjectApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='project-owner', password='test-pass-123')
        self.employee = User.objects.create_user(
            username='assigned-employee',
            first_name='Assigned',
            last_name='Employee',
            password='test-pass-123',
        )
        self.outsider = User.objects.create_user(username='project-outsider', password='test-pass-123')
        self.client.force_authenticate(self.owner)
        response = self.client.post('/api/v1/task-boards/', {'name': 'Shared delivery'}, format='json')
        self.board_id = response.data['id']

    def create_project(self, subtasks=None):
        payload = {
            'board': self.board_id,
            'name': 'Website launch',
            'description': 'Launch the new public website.',
            'assignees': [self.employee.id],
            'subtasks': subtasks or [],
        }
        return self.client.post('/api/v1/projects/', payload, format='json')

    def test_project_creation_adds_shared_kanban_card_subtasks_and_notification(self):
        response = self.create_project(['Approve design', 'Publish content'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        project = Project.objects.get(pk=response.data['id'])
        self.assertEqual(project.kanban_task.title, project.name)
        self.assertEqual(project.kanban_task.parent_task, None)
        self.assertEqual(
            list(project.kanban_task.subtasks.order_by('position').values_list('title', flat=True)),
            ['Approve design', 'Publish content'],
        )
        self.assertTrue(project.assignees.filter(pk=self.employee.pk).exists())
        self.assertTrue(ProjectNotification.objects.filter(project=project, recipient=self.employee).exists())

    def test_subtasks_are_optional(self):
        response = self.create_project()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        project = Project.objects.get(pk=response.data['id'])
        self.assertFalse(project.kanban_task.subtasks.exists())

    def test_assignee_can_open_and_move_the_same_project_card(self):
        created = self.create_project(['Shared checklist item'])
        project = Project.objects.get(pk=created.data['id'])
        done = BoardColumn.objects.get(board_id=self.board_id, name='Done')

        self.client.force_authenticate(self.employee)
        boards = self.client.get('/api/v1/task-boards/')
        tasks = self.client.get(f'/api/v1/tasks/?board={self.board_id}')
        moved = self.client.post(
            f'/api/v1/tasks/{project.kanban_task_id}/move/',
            {'column': done.id, 'position': 0},
            format='json',
        )

        self.assertEqual(boards.status_code, status.HTTP_200_OK)
        self.assertEqual(tasks.status_code, status.HTTP_200_OK)
        self.assertEqual(moved.status_code, status.HTTP_200_OK, moved.data)
        project.kanban_task.refresh_from_db()
        self.assertEqual(project.kanban_task.column, done)

    def test_unassigned_user_cannot_see_project_or_card(self):
        self.create_project()
        self.client.force_authenticate(self.outsider)

        projects = self.client.get(f'/api/v1/projects/?board={self.board_id}')
        tasks = self.client.get(f'/api/v1/tasks/?board={self.board_id}')
        boards = self.client.get('/api/v1/task-boards/')

        self.assertEqual(projects.data['count'], 0)
        self.assertEqual(tasks.data['count'], 0)
        self.assertEqual(boards.data['count'], 0)

    def test_opening_assignment_notification_marks_it_read(self):
        created = self.create_project()
        notification = ProjectNotification.objects.get(project_id=created.data['id'], recipient=self.employee)
        self.client.force_authenticate(None)
        self.client.force_login(self.employee)

        response = self.client.get(f'/tasks/notifications/{notification.id}/open/')

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn(f'board={self.board_id}', response.url)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
