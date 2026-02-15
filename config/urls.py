"""
URL configuration for task_flow_app project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Get admin URL from settings (for security in production)
admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    # Admin
    path(admin_url, admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health Check (for Render.com and monitoring)
    path('api/health/', include('core.urls')),
    
    # API Endpoints
    path('api/', include('tasks.urls')),
    
    # Authentication (JWT)
    path('api/auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
