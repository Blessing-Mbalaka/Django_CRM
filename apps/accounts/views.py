from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse

from .demo import DEFAULT_DEMO_PASSWORD, DEMO_LOGIN_ACCOUNTS
from .forms import LoginForm, ProfileUpdateForm, UJPasswordChangeForm


def login_view(request):
    """Role-aware login — redirects to the academy landing page on success."""
    if request.user.is_authenticated:
        return redirect('academy:index')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Welcome back, {form.get_user().get_full_name()} 👋')
        return redirect(request.GET.get('next') or reverse('academy:index'))

    context = {'form': form}
    if settings.DEBUG:
        context['demo_accounts'] = DEMO_LOGIN_ACCOUNTS
        context['demo_password'] = DEFAULT_DEMO_PASSWORD
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    """POST-only logout for CSRF protection."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been signed out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    form = UJPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/change_password.html', {'form': form})

