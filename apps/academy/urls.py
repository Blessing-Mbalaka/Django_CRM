from django.urls import path

from . import views


app_name = 'academy'

urlpatterns = [
    path('', views.academy_index, name='index'),
    path('certificates/<uuid:verification_id>/', views.certificate_detail, name='certificate'),
]
