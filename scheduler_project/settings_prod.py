"""
Production settings for scheduler_project.
"""

from .settings import *
import os
from datetime import timedelta

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-t-$8%17n6n*-#=$m*tbaf2=@u5m-6prv1%0y_o&9(+&h#k_q(j')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allow specific domains or use environment variable in production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Production security settings
# These will be enabled by default for production, but can be disabled using environment variables
# For example, set ENABLE_SSL=False in .env for local development
ENABLE_SSL = os.environ.get('ENABLE_SSL', 'True').lower() != 'false'

# HTTPS settings
SECURE_SSL_REDIRECT = ENABLE_SSL
SESSION_COOKIE_SECURE = ENABLE_SSL
CSRF_COOKIE_SECURE = ENABLE_SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Configuration
CSRF_COOKIE_DOMAIN = None
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',')
CSRF_USE_SESSIONS = True  # Store CSRF token in the session instead of cookie

# HTTP Strict Transport Security - enable for production
if ENABLE_SSL:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Content Security Policy
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Database - use PostgreSQL in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'scheduler'),
        'USER': os.environ.get('DB_USER', 'scheduler_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            # Use SSL in production but allow disabling for development
            'sslmode': 'require' if os.environ.get('DB_USE_SSL', 'True').lower() != 'false' else 'disable',
            'connect_timeout': 5,
        },
        'ATOMIC_REQUESTS': True,  # Wrap each HTTP request in a transaction
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Media and static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging configuration simplified for Docker environment
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'scheduler': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Security middleware - Enhanced for production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Should be first in the list
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',  # Content Security Policy
    'corsheaders.middleware.CorsMiddleware',  # CORS protection
    'axes.middleware.AxesMiddleware',  # Login attempt security
    'scheduler.middleware.LoginRequiredMiddleware',  # Our custom login protection
]

# REST Framework settings with rate limiting and token authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50
}

# Add WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Setup session expiry 
SESSION_COOKIE_AGE = 43200  # 12 hours in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Enhanced Password Validation for Production
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ["username", "email", "first_name", "last_name"],
            "max_similarity": 0.7,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Password hashers - use more secure algorithms
# Requires: pip install argon2-cffi
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Security Headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
}

# Content Security Policy settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", 'cdn.jsdelivr.net', 'cdn.datatables.net', 'code.jquery.com')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdn.datatables.net', 'fonts.googleapis.com')
CSP_FONT_SRC = ("'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net')
CSP_IMG_SRC = ("'self'", 'data:')
CSP_CONNECT_SRC = ("'self'",)
CSP_INCLUDE_NONCE_IN = ('script-src',)
CSP_EXCLUDE_URL_PREFIXES = ('/admin/',)

# CORS Configuration - restrict to specific domains in production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Rate limiting configuration to prevent abuse
AXES_FAILURE_LIMIT = 5  # Number of login attempts before lockout
AXES_LOCKOUT_TIMEOUT = 30  # Lock out time in minutes
AXES_COOLOFF_TIME = timedelta(minutes=30)  # Time before resetting failure count
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Lock by both user and IP

# Django-ratelimit configuration
RATELIMIT_VIEW = 'scheduler.views.rate_limited_error'  # View to use when rate limit is exceeded
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_FAIL_OPEN = False  # Don't allow requests when the cache is down

# Production Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': False,  # Redis is critical, don't fail silently
        },
        'KEY_PREFIX': 'scheduler',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Use Redis for session cache as well
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
