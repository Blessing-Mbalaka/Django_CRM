from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('',          views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('growth/', views.growth_marketing_view, name='growth_marketing'),
]
