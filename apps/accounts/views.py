from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.db import IntegrityError, transaction
from .models import User
from apps.companies.models import Company
from apps.companies.tenancy import company_context, require_company_admin

from .demo import DEFAULT_DEMO_PASSWORD, DEMO_LOGIN_ACCOUNTS
from .forms import LoginForm, ProfileUpdateForm, UJPasswordChangeForm, CompanyRegistrationForm, CompanyUserCreationForm


def login_view(request):
    """Role-aware login — redirects to the academy landing page on success."""
    if request.user.is_authenticated:
        return redirect('academy:index')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Welcome back, {form.get_user().get_full_name()} 👋')
        target = request.POST.get('next') or request.GET.get('next')
        if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(target)
        return redirect('academy:index')

    context = {'form': form}
    if settings.DEBUG:
        context['demo_accounts'] = DEMO_LOGIN_ACCOUNTS
        context['demo_password'] = DEFAULT_DEMO_PASSWORD
    return render(request, 'accounts/login.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('academy:index')
    form = CompanyRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                company = Company.objects.create(name=form.cleaned_data['company_name'], slug=form.cleaned_data['company_code'], email=form.cleaned_data['email'])
                with company_context(company):
                    owner = form.save(commit=False)
                    owner.company = company
                    owner.role = User.Role.ADMIN
                    owner.save()
        except IntegrityError:
            form.add_error(None, 'That company code or username is already in use.')
        else:
            login(request, owner, backend='apps.accounts.backends.EmailOrUsernameBackend')
            messages.success(request, f'{company.name} is ready. Your company code is {company.slug}.')
            return redirect('academy:index')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def company_users_view(request):
    require_company_admin(request.user)
    form = CompanyUserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.company = request.company
        user.save()
        messages.success(request, 'Team member created. They can sign in with your company code.')
        return redirect('accounts:company_users')
    return render(request, 'accounts/company_users.html', {'form': form, 'team': User.objects.order_by('first_name', 'username')})


class CompanyPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/emails/password_reset_email.txt'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = '/accounts/password-reset/sent/'

    def form_valid(self, form):
        company = Company.objects.filter(slug=self.request.POST.get('company', '').lower(), is_active=True).first()
        if not company:
            form.add_error(None, 'Enter a valid company code.')
            return self.form_invalid(form)
        self.extra_email_context = {'company_code': company.slug}
        with company_context(company):
            return super().form_valid(form)


class CompanyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = '/accounts/password-reset/complete/'

    def dispatch(self, request, *args, **kwargs):
        from django.http import Http404
        from urllib.parse import urlencode
        company = Company.objects.filter(slug=request.GET.get('company', '').lower(), is_active=True).first()
        if not company:
            raise Http404
        with company_context(company):
            response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 302 and 'set-password' in response.url:
            response['Location'] = response.url + '?' + urlencode({'company': company.slug})
        return response


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

