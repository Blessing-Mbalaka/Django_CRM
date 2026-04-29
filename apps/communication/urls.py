from django.urls import path
from . import views
app_name = 'communication'
urlpatterns = [
    path('',    views.comms_health, name='health'),
    path('log/', views.log_contact, name='log'),
]
