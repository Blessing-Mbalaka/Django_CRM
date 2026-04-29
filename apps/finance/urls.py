from django.urls import path
from . import views
app_name = 'finance'
urlpatterns = [
    path('',                 views.finance_overview, name='overview'),
    path('new/',             views.finance_create,   name='create'),
    path('<int:pk>/edit/',   views.finance_edit,     name='edit'),
    path('<int:pk>/delete/', views.finance_delete,   name='delete'),
]
