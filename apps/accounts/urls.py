from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',            views.login_view,           name='login'),
    path('logout/',           views.logout_view,          name='logout'),
    path('profile/',          views.profile_view,         name='profile'),
    path('change-password/',  views.change_password_view, name='change_password'),

    # ── Password Reset Flow (emails printed to console in dev) ──────────────
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/emails/password_reset_email.txt',
            subject_template_name='accounts/emails/password_reset_subject.txt',
            success_url='/accounts/password-reset/sent/',
        ),
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
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/password-reset/complete/',
        ),
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

