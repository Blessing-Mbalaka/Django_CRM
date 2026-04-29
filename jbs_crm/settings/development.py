"""
Development settings — extends base.py
Run with: DJANGO_SETTINGS_MODULE=jbs_crm.settings.development
All secrets (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL) are read from .env
"""
from .base import *  # noqa

