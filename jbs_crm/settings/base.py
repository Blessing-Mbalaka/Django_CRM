"""
JBS CRM — Base Settings
University of Johannesburg | Business School
Phase 1: SQLite + Django REST Framework
"""

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env from project root
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ---------------------------------------------------------------------------
# INSTALLED APPS — Modular app-per-domain structure
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
]

LOCAL_APPS = [
    'apps.accounts',      # Authentication, login, user roles
    'apps.core',          # Dashboard, base views, shared utilities
    'apps.admin_panel',   # System administration, user management
    'apps.staff',         # Staff directory, roles, centre allocation
    'apps.centres',       # Centre profiles, KPIs, performance
    'apps.clients',       # Client & stakeholder profiles
    'apps.engagements',   # Engagement lifecycle management
    'apps.finance',       # Revenue, pipeline, financial tracking
    'apps.alerts',        # Risk alerts, notifications
    'apps.analytics',     # Reporting, forecasting, insights
    'apps.communication', # Relationship health, contact tracking
    'apps.ai',            # Phase 3a — Rule-based AI intelligence layer
    'apps.documents',     # Secure document libraries and file versioning
    'apps.tasks',         # Persistent lightweight Kanban and task activity
    'apps.billing',       # Invoices, invoice lines, and customer payments
    'apps.expenses',      # Expense capture and management approval workflow
    'apps.accounting',    # Double-entry ledger and accounting periods
    'apps.products',      # Shared product and service catalogue
    'apps.inventory',     # Locations, stock movements, and reorder rules
    'apps.purchasing',    # Suppliers, purchase orders, and goods receipts
    'apps.sales',         # Sales orders, fulfilment, and invoice conversion
    'apps.payroll',       # Restricted employee pay profiles, runs, and payslips
    'apps.academy',       # Admin-managed SME Academy courses and modules
    'apps.marketing',     # Campaign planning and communications providers
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jbs_crm.urls'

# ---------------------------------------------------------------------------
# TEMPLATES — Global templates folder + app dirs
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.suite_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'jbs_crm.wsgi.application'

# ---------------------------------------------------------------------------
# DATABASE — SQLite for Phase 1
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

# Optional Marketing credentials; empty values keep planning features available.
TWILIO_EMAIL_API_KEY = env('TWILIO_EMAIL_API_KEY', default='')
TWILIO_EMAIL_API_SECRET = env('TWILIO_EMAIL_API_SECRET', default='')
TWILIO_EMAIL_FROM_ADDRESS = env('TWILIO_EMAIL_FROM_ADDRESS', default='')
TWILIO_EMAIL_FROM_NAME = env('TWILIO_EMAIL_FROM_NAME', default='')
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_API_KEY = env('TWILIO_API_KEY', default='')
TWILIO_API_SECRET = env('TWILIO_API_SECRET', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_SMS_FROM_NUMBER = env('TWILIO_SMS_FROM_NUMBER', default='')
TWILIO_MESSAGING_SERVICE_SID = env('TWILIO_MESSAGING_SERVICE_SID', default='')
TWILIO_STATUS_CALLBACK_URL = env('TWILIO_STATUS_CALLBACK_URL', default='')
META_GRAPH_API_VERSION = env('META_GRAPH_API_VERSION', default='v24.0')
META_ACCESS_TOKEN = env('META_ACCESS_TOKEN', default='')
META_APP_SECRET = env('META_APP_SECRET', default='')
META_WEBHOOK_VERIFY_TOKEN = env('META_WEBHOOK_VERIFY_TOKEN', default='')
META_WHATSAPP_PHONE_NUMBER_ID = env('META_WHATSAPP_PHONE_NUMBER_ID', default='')
META_WHATSAPP_BUSINESS_ACCOUNT_ID = env('META_WHATSAPP_BUSINESS_ACCOUNT_ID', default='')
META_FACEBOOK_PAGE_ID = env('META_FACEBOOK_PAGE_ID', default='')
META_FACEBOOK_PAGE_ACCESS_TOKEN = env('META_FACEBOOK_PAGE_ACCESS_TOKEN', default='')
META_INSTAGRAM_USER_ID = env('META_INSTAGRAM_USER_ID', default='')
META_INSTAGRAM_ACCESS_TOKEN = env('META_INSTAGRAM_ACCESS_TOKEN', default='')
MARKETING_PUBLIC_BASE_URL = env('MARKETING_PUBLIC_BASE_URL', default='')

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/academy/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ---------------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enables the browsable API UI
    ],
}

# ---------------------------------------------------------------------------
# CORS — Allow local development
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL_ORIGINS')

# FOR DEPLOYMENT: Restrict CORS to trusted origins E.G BELOW: 
# CORS_ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
# ]

# ---------------------------------------------------------------------------
# INTERNATIONALISATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-za'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# CRISPY FORMS
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ---------------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# EMAIL — Console backend for dev; swap to SMTP in production via .env
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'JBS CRM <noreply@uj.ac.za>'

# ---------------------------------------------------------------------------
# MESSAGE TAGS — Maps Django messages to Bootstrap alert classes
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}
