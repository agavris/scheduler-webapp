"""
Health check view for Digital Ocean and other deployment platforms.
"""
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError


def health_check(request):
    """
    Simple health check view that verifies:
    1. The web server is running
    2. The database connection is working
    
    Returns 200 OK if everything is fine, 500 if there are issues.
    """
    # Check database connection
    try:
        db_conn = connections['default']
        db_conn.cursor()
        db_status = True
    except OperationalError:
        db_status = False
    
    status = {
        'status': 'ok' if db_status else 'error',
        'database': 'connected' if db_status else 'disconnected',
        'api_version': '1.0',
    }
    
    status_code = 200 if db_status else 500
    
    return JsonResponse(status, status=status_code)
