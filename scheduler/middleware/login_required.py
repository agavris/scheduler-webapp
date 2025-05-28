"""
Login Required Middleware for Django.
Ensures that all views (with specific exceptions) require login.
"""
from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import resolve, reverse


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than those specified in the exempt_urls setting.
    
    Inspired by django-login-required-middleware but simplified for this application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URL paths that should be accessible without authentication
        self.exempt_urls = [
            reverse('login'),  # Login page
            reverse('admin:index'),  # Admin pages
            '/static/',  # Static files
            '/media/',  # Media files
            '/favicon.ico',  # Favicon
        ]
        
        # Add any additional exempt URLs from settings
        if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
            self.exempt_urls.extend(settings.LOGIN_EXEMPT_URLS)
    
    def __call__(self, request):
        # Check if the path should be exempt from login
        path = request.path_info
        
        # Skip middleware for exempted paths
        if any(path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Remember the current URL for post-login redirect
            if not path.startswith('/admin'):  # Don't redirect admin URLs
                request.session['next'] = path
            
            # Redirect to login page
            return HttpResponseRedirect(reverse('login'))
        
        # User is authenticated, continue processing the request
        return self.get_response(request)
