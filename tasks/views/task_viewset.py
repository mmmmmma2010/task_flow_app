"""
ViewSets for Task API.

ViewSets provide:
1. CRUD operations
2. Custom actions
3. Filtering, searching, ordering
4. Pagination
5. Permissions
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import models

from tasks.models import Task, CompletedTask
from tasks.serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskListSerializer,
    CompletedTaskSerializer,
    TaskStatisticsSerializer,
)
from tasks.services import TaskService, CompletedTaskService
from core.permissions import IsOwnerOrReadOnly


@extend_schema_view(
    list=extend_schema(
        summary="List all tasks",
        description="Get a paginated list of tasks with filtering, searching, and ordering.",
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                description='Filter by status (pending, in_progress, completed)',
            ),
            OpenApiParameter(
                name='priority',
                type=OpenApiTypes.STR,
                description='Filter by priority (low, medium, high)',
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in title and description',
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                description='Order by field (e.g., -created_at, priority)',
            ),
        ],
    ),
    create=extend_schema(
        summary="Create a new task",
        description="Create a new task. An email notification will be sent asynchronously.",
    ),
    retrieve=extend_schema(
        summary="Get task details",
        description="Retrieve detailed information about a specific task.",
    ),
    update=extend_schema(
        summary="Update a task",
        description="Update all fields of a task.",
    ),
    partial_update=extend_schema(
        summary="Partially update a task",
        description="Update specific fields of a task.",
    ),
    destroy=extend_schema(
        summary="Delete a task",
        description="Soft delete a task (marks as deleted without removing from database).",
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task model.
    
    Provides:
    - list: GET /api/tasks/
    - create: POST /api/tasks/
    - retrieve: GET /api/tasks/{id}/
    - update: PUT /api/tasks/{id}/
    - partial_update: PATCH /api/tasks/{id}/
    - destroy: DELETE /api/tasks/{id}/
    
    Custom actions:
    - complete: POST /api/tasks/{id}/complete/
    - statistics: GET /api/tasks/statistics/
    - overdue: GET /api/tasks/overdue/
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to', 'created_by']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Get queryset based on user permissions.
        
        Users can see:
        - Tasks they created
        - Tasks assigned to them
        - All tasks if they're staff
        """
        user = self.request.user
        
        if user.is_staff:
            return Task.objects.active()
        
        # Regular users see their own tasks
        return Task.objects.active().filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'statistics':
            return TaskStatisticsSerializer
        return TaskSerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        TaskService.delete_task(instance.id, self.request.user)
    
    @extend_schema(
        summary="Mark task as complete",
        description="Mark a task as completed. Sets status to 'completed' and records completion timestamp.",
        request=None,
        responses={200: TaskSerializer},
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Custom action to mark a task as complete.
        
        POST /api/tasks/{id}/complete/
        """
        task = self.get_object()
        
        try:
            completed_task = TaskService.complete_task(task.id, request.user)
            serializer = TaskSerializer(completed_task, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Get task statistics",
        description="Get statistics about user's tasks (counts by status, priority, etc.).",
        responses={200: TaskStatisticsSerializer},
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get task statistics for the current user.
        
        GET /api/tasks/statistics/
        """
        stats = TaskService.get_task_statistics(request.user)
        serializer = TaskStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get overdue tasks",
        description="Get all overdue tasks for the current user.",
        responses={200: TaskListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get overdue tasks for the current user.
        
        GET /api/tasks/overdue/
        """
        from django.db import models
        
        user = request.user
        
        if user.is_staff:
            overdue_tasks = TaskService.get_overdue_tasks()
        else:
            overdue_tasks = Task.objects.overdue().filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            )
        
        serializer = TaskListSerializer(overdue_tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Bulk assign tasks",
        description="Assign multiple tasks to a user.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'task_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'List of task IDs to assign',
                    },
                    'assigned_to_id': {
                        'type': 'integer',
                        'description': 'ID of user to assign tasks to',
                    },
                },
                'required': ['task_ids', 'assigned_to_id'],
            }
        },
        responses={200: TaskSerializer(many=True)},
    )
    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """
        Bulk assign tasks to a user.
        
        POST /api/tasks/bulk_assign/
        Body: {
            "task_ids": [1, 2, 3],
            "assigned_to_id": 5
        }
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        task_ids = request.data.get('task_ids', [])
        assigned_to_id = request.data.get('assigned_to_id')
        
        if not task_ids or not assigned_to_id:
            return Response(
                {'error': 'task_ids and assigned_to_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id)
            updated_tasks = TaskService.bulk_assign_tasks(
                task_ids=task_ids,
                assigned_to=assigned_to,
                user=request.user
            )
            
            serializer = TaskSerializer(updated_tasks, many=True, context={'request': request})
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': f'User with id {assigned_to_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(
        summary="List completed tasks",
        description="Get a paginated list of completed tasks.",
    ),
    retrieve=extend_schema(
        summary="Get completed task details",
        description="Retrieve detailed information about a specific completed task.",
    ),
)
class CompletedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for CompletedTask proxy model.
    
    This demonstrates how proxy models can have their own API endpoints
    with specialized behavior.
    
    Provides:
    - list: GET /api/completed-tasks/
    - retrieve: GET /api/completed-tasks/{id}/
    
    Custom actions:
    - recent: GET /api/completed-tasks/recent/
    - report: GET /api/completed-tasks/report/
    """
    
    serializer_class = CompletedTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['priority', 'created_by']
    ordering_fields = ['completed_at', 'created_at']
    ordering = ['-completed_at']
    
    def get_queryset(self):
        """Get completed tasks for the current user."""
        from django.db import models
        
        user = self.request.user
        
        if user.is_staff:
            return CompletedTask.objects.all()
        
        return CompletedTask.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        )
    
    @extend_schema(
        summary="Get recently completed tasks",
        description="Get tasks completed in the last N days (default: 7).",
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                description='Number of days to look back (default: 7)',
            ),
        ],
        responses={200: CompletedTaskSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recently completed tasks.
        
        GET /api/completed-tasks/recent/?days=7
        """
        days = int(request.query_params.get('days', 7))
        recent_tasks = CompletedTask.objects.recent(days=days)
        
        # Filter by user if not staff
        from django.db import models
        if not request.user.is_staff:
            recent_tasks = recent_tasks.filter(
                models.Q(created_by=request.user) | models.Q(assigned_to=request.user)
            )
        
        serializer = self.get_serializer(recent_tasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get completion report",
        description="Get a completion report for the current user.",
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                description='Number of days to include in report (default: 30)',
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def report(self, request):
        """
        Get completion report for the current user.
        
        GET /api/completed-tasks/report/?days=30
        """
        days = int(request.query_params.get('days', 30))
        report = CompletedTaskService.get_completion_report(request.user, days=days)
        return Response(report)
