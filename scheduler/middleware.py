"""
Custom middleware for the scheduler application.
"""
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Middleware to require login for all pages except those in the exempted URLs.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempted_urls = [
            'login', 
            'logout',
            'user_preferences',  # User preferences page
            'admin:index',
            'admin:login',
            'static',  # Static files
        ]
        
        # Paths that should be accessible without login
        self.exempted_paths = [
            '/static/',  # Static files
            '/media/',   # Media files
            '/admin/',   # Admin panel (has its own auth)
            '/api-auth/', # DRF authentication
        ]

    def __call__(self, request):
        # Process request before the view is called
        if not request.user.is_authenticated:
            # First check if the path starts with any exempted paths
            for path in self.exempted_paths:
                if request.path_info.startswith(path):
                    return self.get_response(request)
            
            # Then check for exempted URL names
            try:
                current_url_name = resolve(request.path_info).url_name
                if current_url_name in self.exempted_urls:
                    return self.get_response(request)
            except:
                # If URL resolution fails, default to requiring login
                pass
                
            # If we get here, the URL is not exempted, so redirect to login
            login_url = f"{reverse('login')}?next={request.path}"
            return redirect(login_url)
        
        response = self.get_response(request)
        return response
