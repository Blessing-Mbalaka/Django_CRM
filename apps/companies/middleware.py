from django.contrib.auth.views import redirect_to_login
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.utils.cache import patch_cache_control

from .tenancy import company_context


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if not user.is_authenticated and request.path.startswith('/api/'):
            from rest_framework.authentication import TokenAuthentication
            from rest_framework.exceptions import AuthenticationFailed
            try:
                auth = TokenAuthentication().authenticate(request)
            except AuthenticationFailed:
                auth = None
            if auth:
                user, request.company_token = auth
                # Scope early, but let DRF perform token authentication itself.
                # Setting Django's session user here would incorrectly trigger
                # SessionAuthentication's CSRF checks for token-only API writes.
        company = user.company if user.is_authenticated else None
        request.company = company
        if user.is_authenticated and (not company or not company.is_active):
            if request.path == '/accounts/logout/':
                return self.get_response(request)
            if request.session.get('_auth_user_id'):
                logout(request)
            return HttpResponseForbidden('Your company is unavailable. <a href="/accounts/login/">Sign in again</a> or contact support.')
        # Only signed provider callbacks can select their target company.
        if request.path.startswith('/growth/webhooks/'):
            from .models import Company
            code = request.GET.get('company', 'original')
            company = Company.objects.filter(slug=code, is_active=True).first()
            if not company:
                return HttpResponseForbidden()
            request.company = company
        public = request.path.startswith(('/accounts/', '/api/', '/static/', '/growth/webhooks/'))
        if not public and not user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        with company_context(company):
            response = self.get_response(request)
            if user.is_authenticated:
                patch_cache_control(response, private=True, no_store=True)
            if getattr(response, 'streaming', False):
                content = response.streaming_content
                def stream():
                    with company_context(company):
                        yield from content
                response.streaming_content = stream()
            return response
