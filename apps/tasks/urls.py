from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [path('', views.board_view, name='board')]

