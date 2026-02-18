"""
Production settings - extends base settings with production-specific configurations.
"""

from .base import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',') + ['.vercel.app']

# Database configuration from DATABASE_URL (Render.com provides this)
if config('DATABASE_URL', default=None):
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS Configuration (if you have a frontend)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
CORS_ALLOW_CREDENTIALS = True

# Email Configuration (use real SMTP in production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Sentry Integration (Optional - for error tracking)
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Logging - Send errors to file and console
LOGGING['handlers']['file']['filename'] = '/var/log/django/django.log'

# Cache timeout - longer in production
CACHES['default']['TIMEOUT'] = 600  # 10 minutes

# Admin URL (change for security)
ADMIN_URL = config('ADMIN_URL', default='admin/')
