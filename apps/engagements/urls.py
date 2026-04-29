from django.urls import path
from . import views
app_name = 'engagements'
urlpatterns = [
    path('',                 views.engagement_list,   name='list'),
    path('new/',             views.engagement_create, name='create'),
    path('<int:pk>/',        views.engagement_detail, name='detail'),
    path('<int:pk>/edit/',   views.engagement_edit,   name='edit'),
    path('<int:pk>/delete/', views.engagement_delete, name='delete'),
]
