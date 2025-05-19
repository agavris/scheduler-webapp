"""
Sentry integration for error tracking in production.
"""
import logging
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

logger = logging.getLogger(__name__)

def initialize_sentry():
    """
    Initialize Sentry SDK for error tracking.
    
    This should be called in settings.py when in production mode.
    """
    sentry_dsn = os.environ.get('SENTRY_DSN')
    
    if not sentry_dsn:
        logger.warning("Sentry DSN not configured. Error tracking disabled.")
        return
        
    # Configure Sentry SDK
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.5,
        
        # Send environment info
        environment=os.environ.get('DJANGO_ENV', 'production'),
        
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        
        # By default the SDK will try to use the SENTRY_RELEASE
        # environment variable, or infer a git commit
        # SHA as release, however you may want to set
        # something more human-readable.
        release=os.environ.get('APP_VERSION', '1.0.0'),
    )
    
    logger.info("Sentry initialized for error tracking.")
