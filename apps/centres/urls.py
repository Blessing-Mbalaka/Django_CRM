from django.urls import path
from . import views
app_name = 'centres'
urlpatterns = [
    path('',                 views.centre_list,   name='list'),
    path('new/',             views.centre_create, name='create'),
    path('<int:pk>/',        views.centre_detail, name='detail'),
    path('<int:pk>/edit/',   views.centre_edit,   name='edit'),
    path('<int:pk>/delete/', views.centre_delete, name='delete'),
]
