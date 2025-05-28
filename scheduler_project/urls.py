"""
URL configuration for scheduler_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from scheduler.views.health import health_check
# Import other views if needed

# Simple URL patterns for development
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('scheduler.urls')),
    
    # Authentication URLs - registration restricted to admin only
    path('login/', auth_views.LoginView.as_view(template_name='scheduler/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/', template_name='scheduler/login.html', extra_context={'logout_message': 'You have been successfully logged out.'}), name='logout'),
    
    # Health check for Digital Ocean and other deployment platforms
    path('health/', health_check, name='health_check'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
