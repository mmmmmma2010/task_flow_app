from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from tasks.serializers.task_serializer import UserSerializer

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User model (read-only).
    Allows authenticated users to list all users to populate assignment dropdowns.
    """
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for dropdown lists
