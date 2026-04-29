from django.urls import path
from . import views
app_name = 'staff'
urlpatterns = [
    path('',                 views.staff_list,   name='list'),
    path('new/',             views.staff_create, name='create'),
    path('<int:pk>/',        views.staff_detail, name='detail'),
    path('<int:pk>/edit/',   views.staff_edit,   name='edit'),
    path('<int:pk>/delete/', views.staff_delete, name='delete'),
]
