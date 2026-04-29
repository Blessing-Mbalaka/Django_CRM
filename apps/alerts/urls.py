from django.urls import path
from . import views

app_name = 'alerts'
urlpatterns = [
    path('',                    views.alert_list,         name='list'),
    path('new/',                views.alert_create,       name='create'),
    path('run-pipeline/',       views.run_alert_pipeline, name='run_pipeline'),
    path('<int:pk>/',           views.alert_detail,       name='detail'),
    path('<int:pk>/edit/',      views.alert_edit,         name='edit'),
    path('<int:pk>/delete/',    views.alert_delete,       name='delete'),
    path('<int:pk>/resolve/',   views.alert_resolve,      name='resolve'),
]
