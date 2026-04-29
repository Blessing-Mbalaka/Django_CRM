from django.urls import path
from . import views
app_name = 'admin_panel'
urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/<int:pk>/toggle/', views.toggle_user_active, name='toggle_user'),
]

