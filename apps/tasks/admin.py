from django.contrib import admin

from .models import Board, BoardColumn, Project, ProjectNotification, Task, TaskActivity, TaskComment

admin.site.register([Board, BoardColumn, Task, TaskComment, TaskActivity, Project, ProjectNotification])
