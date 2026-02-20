"""
Development settings - extends base settings with development-specific configurations.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# CORS Headers for local development (if frontend is separate)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',  # Vite dev server
    'http://localhost:8080',
    
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',  # Vite dev server
    'http://127.0.0.1:8080',
]

CORS_ALLOW_CREDENTIALS = False

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable some security features for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Show more detailed error pages
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Less strict throttling for development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '10000/hour',
}

# Celery eager mode for development (tasks run synchronously)
# Uncomment if you want to test without running celery worker
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True
