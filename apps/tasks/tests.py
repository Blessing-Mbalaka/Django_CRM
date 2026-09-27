from pathlib import Path
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.contrib.staticfiles import finders
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Board, BoardColumn, Project, ProjectNotification, Task


class TaskLifecycleModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='task-lifecycle', password='test-pass-123')
        self.client.force_authenticate(self.user)

    def test_new_project_defaults_to_planning_with_start_date(self):
        board = Board.objects.create(name='Lifecycle', owner=self.user)

        project = Project.objects.create(board=board, name='Launch', created_by=self.user)

        self.assertEqual(project.status, 'planning')
        self.assertEqual(project.start_date, date.today())

    def test_project_rejects_due_date_before_start_date(self):
        board = Board.objects.create(name='Dates', owner=self.user)
        project = Project(
            board=board,
            name='Impossible schedule',
            created_by=self.user,
            start_date=date.today(),
            due_date=date.today() - timedelta(days=1),
        )

        with self.assertRaisesMessage(ValidationError, 'Due date cannot be before the start date.'):
            project.full_clean()

    def test_new_board_has_exact_three_columns(self):
        response = self.client.post('/api/v1/task-boards/', {'name': 'Three states'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            list(BoardColumn.objects.filter(board_id=response.data['id']).values_list('name', flat=True)),
            ['To Do', 'In Progress', 'Completed'],
        )


class TaskThreeStateMigrationTests(TransactionTestCase):
    migrate_from = [('tasks', '0002_project_projectnotification_task_parent_task')]
    migrate_to = [('tasks', '0003_project_lifecycle_three_state')]

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        old_apps = self.executor.loader.project_state(self.migrate_from).apps
        UserModel = old_apps.get_model('accounts', 'User')
        BoardModel = old_apps.get_model('tasks', 'Board')
        ColumnModel = old_apps.get_model('tasks', 'BoardColumn')
        TaskModel = old_apps.get_model('tasks', 'Task')
        ActivityModel = old_apps.get_model('tasks', 'TaskActivity')

        user = UserModel.objects.create(username='migration-owner', password='unused')
        board = BoardModel.objects.create(name='Legacy board', owner_id=user.pk)
        names = ['Backlog', 'To Do', 'In Progress', 'Blocked', 'Done', 'Review']
        columns = [
            ColumnModel.objects.create(board=board, name=name, position=index)
            for index, name in enumerate(names)
        ]
        self.task_ids = []
        for index, column in enumerate(columns):
            task = TaskModel.objects.create(
                board=board,
                column=column,
                title=f'Legacy {names[index]}',
                position=0,
                creator_id=user.pk,
            )
            self.task_ids.append(task.pk)
        ActivityModel.objects.create(
            task_id=self.task_ids[0], actor_id=user.pk, action='created', detail={'source': 'legacy'}
        )
        self.board_id = board.pk

        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        self.apps = self.executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(self.migrate_to)
        super().tearDown()

    def test_migration_preserves_tasks_and_maps_every_column(self):
        ColumnModel = self.apps.get_model('tasks', 'BoardColumn')
        TaskModel = self.apps.get_model('tasks', 'Task')
        ActivityModel = self.apps.get_model('tasks', 'TaskActivity')

        self.assertEqual(
            list(ColumnModel.objects.filter(board_id=self.board_id).values_list('name', 'position')),
            [('To Do', 0), ('In Progress', 1), ('Completed', 2)],
        )
        self.assertEqual(set(TaskModel.objects.values_list('id', flat=True)), set(self.task_ids))
        self.assertEqual(
            list(TaskModel.objects.filter(column__name='To Do').values_list('title', 'position')),
            [('Legacy Backlog', 0), ('Legacy To Do', 1)],
        )
        self.assertEqual(
            list(TaskModel.objects.filter(column__name='In Progress').values_list('title', 'position')),
            [('Legacy In Progress', 0), ('Legacy Blocked', 1), ('Legacy Review', 2)],
        )
        self.assertEqual(
            list(TaskModel.objects.filter(column__name='Completed').values_list('title', 'position')),
            [('Legacy Done', 0)],
        )
        self.assertEqual(ActivityModel.objects.filter(task_id=self.task_ids[0], action='created').count(), 1)


class TaskCompletionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='completion-owner', password='test-pass-123')
        self.client.force_authenticate(self.user)
        board_response = self.client.post('/api/v1/task-boards/', {'name': 'Completion'}, format='json')
        self.board_id = board_response.data['id']
        self.todo = BoardColumn.objects.get(board_id=self.board_id, name='To Do')
        self.progress = BoardColumn.objects.get(board_id=self.board_id, name='In Progress')
        self.completed = BoardColumn.objects.get(board_id=self.board_id, name='Completed')
        task_response = self.client.post(
            '/api/v1/tasks/',
            {'board': self.board_id, 'column': self.todo.id, 'title': 'Finish me'},
            format='json',
        )
        self.task_id = task_response.data['id']

    def test_move_to_completed_sets_completed_at(self):
        response = self.client.post(
            f'/api/v1/tasks/{self.task_id}/move/',
            {'column': self.completed.id, 'position': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Task.objects.get(pk=self.task_id).completed_at)

    def test_move_out_of_completed_clears_completed_at(self):
        Task.objects.filter(pk=self.task_id).update(column=self.completed, completed_at=timezone.now())

        response = self.client.post(
            f'/api/v1/tasks/{self.task_id}/move/',
            {'column': self.progress.id, 'position': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(Task.objects.get(pk=self.task_id).completed_at)


class ProjectLifecycleApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='project-lifecycle-owner', password='test-pass-123')
        self.assignee = User.objects.create_user(username='project-lifecycle-assignee', password='test-pass-123')
        self.client.force_authenticate(self.owner)
        self.board_id = self.client.post(
            '/api/v1/task-boards/', {'name': 'Project lifecycle'}, format='json'
        ).data['id']

    def project_payload(self, **overrides):
        payload = {
            'board': self.board_id,
            'name': 'Launch project',
            'assignees': [self.assignee.id],
            'start_date': '2026-10-01',
            'due_date': '2026-10-31',
            'status': 'active',
        }
        payload.update(overrides)
        return payload

    def test_project_due_date_must_not_precede_start(self):
        response = self.client.post(
            '/api/v1/projects/',
            self.project_payload(due_date='2026-09-30'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)

    def test_owner_can_update_project_lifecycle(self):
        created = self.client.post('/api/v1/projects/', self.project_payload(), format='json')

        response = self.client.patch(
            f"/api/v1/projects/{created.data['id']}/",
            {'status': 'completed', 'due_date': '2026-11-07'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(pk=created.data['id'])
        self.assertEqual(project.status, Project.Status.COMPLETED)
        self.assertEqual(project.due_date.isoformat(), '2026-11-07')


class TaskApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tasks', password='test-pass-123')
        self.client.force_authenticate(self.user)

    def test_board_creates_default_columns_and_task_move_persists(self):
        board_response = self.client.post('/api/task-boards/', {'name': 'Operations'}, format='json')
        self.assertEqual(board_response.status_code, status.HTTP_201_CREATED)
        board_id = board_response.data['id']
        columns = BoardColumn.objects.filter(board_id=board_id)
        self.assertEqual(columns.count(), 3)
        todo = columns.get(name='To Do')
        completed = columns.get(name='Completed')
        task_response = self.client.post('/api/tasks/', {'board': board_id, 'column': todo.id, 'title': 'Send invoice'}, format='json')
        self.assertEqual(task_response.status_code, status.HTTP_201_CREATED)
        move = self.client.post(f"/api/tasks/{task_response.data['id']}/move/", {'column': completed.id, 'position': 0}, format='json')
        self.assertEqual(move.status_code, status.HTTP_200_OK)
        task = Task.objects.get(pk=task_response.data['id'])
        self.assertEqual(task.column, completed)
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
        completed = BoardColumn.objects.get(board_id=self.board_id, name='Completed')

        self.client.force_authenticate(self.employee)
        boards = self.client.get('/api/v1/task-boards/')
        tasks = self.client.get(f'/api/v1/tasks/?board={self.board_id}')
        moved = self.client.post(
            f'/api/v1/tasks/{project.kanban_task_id}/move/',
            {'column': completed.id, 'position': 0},
            format='json',
        )

        self.assertEqual(boards.status_code, status.HTTP_200_OK)
        self.assertEqual(tasks.status_code, status.HTTP_200_OK)
        self.assertEqual(moved.status_code, status.HTTP_200_OK, moved.data)
        project.kanban_task.refresh_from_db()
        self.assertEqual(project.kanban_task.column, completed)

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
