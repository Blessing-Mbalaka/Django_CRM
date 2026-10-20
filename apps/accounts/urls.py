from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',            views.login_view,           name='login'),
    path('register/', views.register_view, name='register'),
    path('team/', views.company_users_view, name='company_users'),
    path('logout/',           views.logout_view,          name='logout'),
    path('profile/',          views.profile_view,         name='profile'),
    path('change-password/',  views.change_password_view, name='change_password'),

    # ── Password Reset Flow (emails printed to console in dev) ──────────────
    path(
        'password-reset/',
        views.CompanyPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password-reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        views.CompanyPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]

