"""
URL configuration for tasks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from tasks.views import TaskViewSet, CompletedTaskViewSet, UserViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'completed-tasks', CompletedTaskViewSet, basename='completed-task')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints (from router)
    path('', include(router.urls)),
]
