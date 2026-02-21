"""
Custom QuerySet and Manager for Task model.

This module provides custom database query methods and filters
to encapsulate common query patterns and improve code reusability.
"""

from django.db import models
from django.utils import timezone


class TaskQuerySet(models.QuerySet):
    """
    Custom QuerySet for Task model with chainable filters.
    
    This allows for composable queries like:
    Task.objects.active().high_priority().overdue()
    """
    
    def active(self):
        """Return only non-deleted tasks."""
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """Return only soft-deleted tasks."""
        return self.filter(is_deleted=True)
    
    def completed(self):
        """Return only completed tasks."""
        return self.filter(status='completed', is_deleted=False)
    
    def pending(self):
        """Return only pending tasks."""
        return self.filter(status='pending', is_deleted=False)
    
    def in_progress(self):
        """Return only in-progress tasks."""
        return self.filter(status='in_progress', is_deleted=False)
    
    def overdue(self):
        """Return tasks that are past their due date and not completed."""
        return self.filter(
            due_date__lt=timezone.now(),
            is_deleted=False
        ).exclude(status='completed')
    
    def by_priority(self, priority):
        """Filter tasks by priority level."""
        return self.filter(priority=priority, is_deleted=False)
    
    def high_priority(self):
        """Return high priority tasks."""
        return self.by_priority('high')
    
    def medium_priority(self):
        """Return medium priority tasks."""
        return self.by_priority('medium')
    
    def low_priority(self):
        """Return low priority tasks."""
        return self.by_priority('low')
    
    def created_by_user(self, user):
        """Return tasks created by a specific user."""
        return self.filter(created_by=user, is_deleted=False)
    
    def assigned_to_user(self, user):
        """Return tasks assigned to a specific user."""
        return self.filter(assigned_to=user, is_deleted=False)


class TaskManager(models.Manager.from_queryset(TaskQuerySet)):
    """
    Custom Manager for Task model.
    
    Provides default filtering and custom query methods by inheriting
    from TaskQuerySet.
    """
    pass


class CompletedTaskManager(models.Manager):
    """
    Custom Manager for CompletedTask proxy model.
    
    This manager automatically filters to show only completed tasks,
    demonstrating the power of proxy models for different views of the same data.
    """
    
    def get_queryset(self):
        """Override to return only completed tasks."""
        return TaskQuerySet(self.model, using=self._db).filter(
            status='completed',
            is_deleted=False
        )
    
    def recent(self, days=7):
        """Return recently completed tasks (default: last 7 days)."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.get_queryset().filter(completed_at__gte=cutoff_date)
    
    def by_user(self, user):
        """Return completed tasks by a specific user."""
        return self.get_queryset().filter(created_by=user)
    
    def archived(self):
        """Return completed tasks older than 30 days (archivable)."""
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        return self.get_queryset().filter(completed_at__lt=cutoff_date)
