"""
Task Service Layer.

This module contains business logic for task operations.
It separates business logic from views, making it reusable and testable.

WHY SERVICE LAYER?
==================

The service layer pattern provides several benefits:

1. **Separation of Concerns**: Views handle HTTP, services handle business logic
2. **Reusability**: Same logic can be used from API, CLI, admin, etc.
3. **Testability**: Business logic can be tested without HTTP layer
4. **Single Source of Truth**: Business rules defined in one place
5. **Transaction Management**: Complex operations wrapped in transactions
6. **Async Task Coordination**: Services trigger background tasks

ARCHITECTURE:
=============

View Layer (API)
    ↓
Service Layer (Business Logic) ← You are here
    ↓
Model Layer (Data Access)
    ↓
Database

Services also coordinate with:
- Celery Tasks (async operations)
- Cache Layer (performance)
- External APIs (integrations)
"""

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from typing import Optional, List, Dict, Any
import logging

from tasks.models import Task, CompletedTask
from core.exceptions import (
    TaskNotFoundError,
    TaskAlreadyCompletedError,
    InvalidTaskStatusError,
    ServiceError,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class TaskService:
    """
    Service class for task-related business operations.
    
    This class encapsulates all business logic for task management,
    including creation, updates, completion, and deletion.
    """
    
    # Cache keys
    CACHE_KEY_TASK = 'task:{task_id}'
    CACHE_KEY_USER_TASKS = 'user_tasks:{user_id}'
    CACHE_KEY_OVERDUE_TASKS = 'overdue_tasks'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    @transaction.atomic
    def create_task(
        title: str,
        created_by: User,
        description: str = '',
        priority: str = Task.PRIORITY_MEDIUM,
        status: str = Task.STATUS_PENDING,
        due_date: Optional[timezone.datetime] = None,
        assigned_to: Optional[User] = None,
    ) -> Task:
        """
        Create a new task and trigger notification.
        
        This method:
        1. Creates the task in the database
        2. Invalidates relevant caches
        3. Triggers async email notification
        
        Args:
            title: Task title
            created_by: User creating the task
            description: Task description
            priority: Task priority (low, medium, high)
            status: Initial status (default: pending)
            due_date: When task should be completed
            assigned_to: User assigned to the task
        
        Returns:
            Task: The created task instance
        
        Raises:
            ServiceError: If task creation fails
        """
        try:
            # Create the task
            task = Task.objects.create(
                title=title,
                description=description,
                priority=priority,
                status=status,
                due_date=due_date,
                created_by=created_by,
                assigned_to=assigned_to,
            )
            
            logger.info(f"Task created: {task.id} - {task.title} by {created_by.username}")
            
            # Invalidate caches
            TaskService._invalidate_user_cache(created_by.id)
            if assigned_to:
                TaskService._invalidate_user_cache(assigned_to.id)
            
            # Trigger async notification (Celery task)
            from tasks.tasks import send_task_created_notification
            send_task_created_notification.delay(task.id)
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise ServiceError(f"Failed to create task: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def update_task(
        task_id: int,
        user: User,
        **update_fields
    ) -> Task:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            user: User performing the update
            **update_fields: Fields to update
        
        Returns:
            Task: The updated task instance
        
        Raises:
            TaskNotFoundError: If task doesn't exist
            ServiceError: If update fails
        """
        try:
            task = Task.objects.active().get(id=task_id)
            
            # Update fields
            for field, value in update_fields.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            
            task.save()
            
            logger.info(f"Task updated: {task.id} by {user.username}")
            
            # Invalidate caches
            TaskService._invalidate_task_cache(task_id)
            TaskService._invalidate_user_cache(task.created_by.id)
            if task.assigned_to:
                TaskService._invalidate_user_cache(task.assigned_to.id)
            
            return task
            
        except Task.DoesNotExist:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            raise ServiceError(f"Failed to update task: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def complete_task(task_id: int, user: User) -> Task:
        """
        Mark a task as completed.
        
        This is a specific business operation that:
        1. Changes status to completed
        2. Sets completed_at timestamp
        3. Invalidates caches
        4. Could trigger completion notifications
        
        Args:
            task_id: ID of the task to complete
            user: User completing the task
        
        Returns:
            Task: The completed task instance
        
        Raises:
            TaskNotFoundError: If task doesn't exist
            TaskAlreadyCompletedError: If task is already completed
        """
        try:
            task = Task.objects.active().get(id=task_id)
            
            # Check if already completed
            if task.status == Task.STATUS_COMPLETED:
                raise TaskAlreadyCompletedError()
            
            # Mark as complete
            task.mark_complete()
            
            logger.info(f"Task completed: {task.id} by {user.username}")
            
            # Invalidate caches
            TaskService._invalidate_task_cache(task_id)
            TaskService._invalidate_user_cache(task.created_by.id)
            cache.delete(TaskService.CACHE_KEY_OVERDUE_TASKS)
            
            return task
            
        except Task.DoesNotExist:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
    
    @staticmethod
    @transaction.atomic
    def delete_task(task_id: int, user: User) -> None:
        """
        Soft delete a task.
        
        Args:
            task_id: ID of the task to delete
            user: User deleting the task
        
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        try:
            task = Task.objects.active().get(id=task_id)
            task.soft_delete()
            
            logger.info(f"Task deleted: {task.id} by {user.username}")
            
            # Invalidate caches
            TaskService._invalidate_task_cache(task_id)
            TaskService._invalidate_user_cache(task.created_by.id)
            
        except Task.DoesNotExist:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
    
    @staticmethod
    def get_task(task_id: int, use_cache: bool = True) -> Task:
        """
        Get a task by ID with optional caching.
        
        Args:
            task_id: ID of the task
            use_cache: Whether to use cache
        
        Returns:
            Task: The task instance
        
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        cache_key = TaskService.CACHE_KEY_TASK.format(task_id=task_id)
        
        if use_cache:
            task = cache.get(cache_key)
            if task:
                return task
        
        try:
            task = Task.objects.active().get(id=task_id)
            
            if use_cache:
                cache.set(cache_key, task, TaskService.CACHE_TIMEOUT)
            
            return task
            
        except Task.DoesNotExist:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
    
    @staticmethod
    def get_overdue_tasks(use_cache: bool = True) -> List[Task]:
        """
        Get all overdue tasks with optional caching.
        
        Args:
            use_cache: Whether to use cache
        
        Returns:
            List[Task]: List of overdue tasks
        """
        if use_cache:
            tasks = cache.get(TaskService.CACHE_KEY_OVERDUE_TASKS)
            if tasks is not None:
                return tasks
        
        tasks = list(Task.objects.overdue())
        
        if use_cache:
            cache.set(
                TaskService.CACHE_KEY_OVERDUE_TASKS,
                tasks,
                TaskService.CACHE_TIMEOUT
            )
        
        return tasks
    
    @staticmethod
    @transaction.atomic
    def bulk_assign_tasks(task_ids: List[int], assigned_to: User, user: User) -> List[Task]:
        """
        Bulk assign multiple tasks to a user.
        
        This demonstrates a complex business operation that:
        1. Updates multiple tasks in a transaction
        2. Invalidates multiple caches
        3. Could trigger bulk notifications
        
        Args:
            task_ids: List of task IDs to assign
            assigned_to: User to assign tasks to
            user: User performing the assignment
        
        Returns:
            List[Task]: List of updated tasks
        """
        tasks = Task.objects.active().filter(id__in=task_ids)
        updated_tasks = []
        
        for task in tasks:
            task.assigned_to = assigned_to
            task.save()
            updated_tasks.append(task)
            
            # Invalidate cache
            TaskService._invalidate_task_cache(task.id)
        
        # Invalidate user cache
        TaskService._invalidate_user_cache(assigned_to.id)
        
        logger.info(
            f"Bulk assigned {len(updated_tasks)} tasks to {assigned_to.username} "
            f"by {user.username}"
        )
        
        return updated_tasks
    
    @staticmethod
    def get_task_statistics(user: User) -> Dict[str, Any]:
        """
        Get task statistics for a user.
        
        Args:
            user: User to get statistics for
        
        Returns:
            Dict: Statistics including counts by status, priority, etc.
        """
        user_tasks = Task.objects.created_by_user(user)
        
        return {
            'total': user_tasks.count(),
            'pending': user_tasks.pending().count(),
            'in_progress': user_tasks.in_progress().count(),
            'completed': user_tasks.completed().count(),
            'overdue': user_tasks.overdue().count(),
            'high_priority': user_tasks.high_priority().count(),
        }
    
    # Cache management helpers
    
    @staticmethod
    def _invalidate_task_cache(task_id: int) -> None:
        """Invalidate cache for a specific task."""
        cache_key = TaskService.CACHE_KEY_TASK.format(task_id=task_id)
        cache.delete(cache_key)
    
    @staticmethod
    def _invalidate_user_cache(user_id: int) -> None:
        """Invalidate cache for a user's tasks."""
        cache_key = TaskService.CACHE_KEY_USER_TASKS.format(user_id=user_id)
        cache.delete(cache_key)


class CompletedTaskService:
    """
    Service class for completed task operations.
    
    This demonstrates how proxy models can have their own service layer
    with specialized business logic.
    """
    
    @staticmethod
    def get_completion_report(user: User, days: int = 30) -> Dict[str, Any]:
        """
        Generate a completion report for a user.
        
        Args:
            user: User to generate report for
            days: Number of days to include in report
        
        Returns:
            Dict: Completion statistics and summary
        """
        completed_tasks = CompletedTask.objects.by_user(user).recent(days=days)
        
        return {
            'user': user.username,
            'period_days': days,
            'total_completed': completed_tasks.count(),
            'tasks': [task.get_completion_summary() for task in completed_tasks[:10]],
        }
    
    @staticmethod
    @transaction.atomic
    def archive_old_tasks(days: int = 30) -> int:
        """
        Archive completed tasks older than specified days.
        
        Args:
            days: Archive tasks completed more than this many days ago
        
        Returns:
            int: Number of tasks archived
        """
        archivable_tasks = CompletedTask.objects.archived()
        count = 0
        
        for task in archivable_tasks:
            try:
                task.archive()
                count += 1
            except ValueError as e:
                logger.warning(f"Could not archive task {task.id}: {str(e)}")
        
        logger.info(f"Archived {count} old completed tasks")
        return count
