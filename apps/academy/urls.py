from django.urls import path

from . import views


app_name = 'academy'

urlpatterns = [
    path('', views.academy_index, name='index'),
]

