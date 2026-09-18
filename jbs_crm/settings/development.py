"""
Development settings — extends base.py
Run with: DJANGO_SETTINGS_MODULE=jbs_crm.settings.development
All secrets (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL) are read from .env
"""
from .base import *  # noqa

# The development settings module must always serve local static assets. The
# production module explicitly sets DEBUG=False and retains its hardening.
DEBUG = True

