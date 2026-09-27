from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.board_view, name='board'),
    path('attachments/<int:pk>/download/', views.download_attachment, name='attachment_download'),
    path('notifications/<int:pk>/open/', views.open_project_notification, name='open_notification'),
]
