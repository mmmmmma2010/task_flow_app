"""
CompletedTask Proxy Model.

This module demonstrates the use of Django proxy models to provide
a different interface to the same database table.

WHY PROXY MODEL?
================

A proxy model is used when you want to:
1. Change the default behavior of a model (different manager, methods)
2. Provide a different interface without creating a new database table
3. Have different admin representations of the same data
4. Optimize queries for specific use cases

PROXY vs ABSTRACT INHERITANCE:
- Abstract: Creates separate tables for each child model (data duplication)
- Proxy: Uses the same table, just different Python behavior

PROXY vs MULTI-TABLE INHERITANCE:
- Multi-table: Creates additional table with JOIN overhead
- Proxy: No additional table, no JOINs, better performance

USE CASE FOR CompletedTask:
===========================

The CompletedTask proxy model provides:
1. A specialized manager that only returns completed tasks
2. Custom methods specific to completed tasks (archiving, reporting)
3. Different admin interface for managing completed tasks
4. Optimized queries for completed task operations
5. Cleaner API endpoints (/api/completed-tasks/ vs /api/tasks/?status=completed)

This is better than filtering Task.objects.filter(status='completed') because:
- Encapsulates the filtering logic in one place
- Provides a semantic interface (CompletedTask vs Task)
- Allows for specialized methods without cluttering the base Task model
- Enables different permissions and access patterns
"""

from django.db import models
from django.utils import timezone
from .task import Task
from .managers import CompletedTaskManager


class CompletedTask(Task):
    """
    Proxy model for completed tasks.
    
    This model uses the same database table as Task but provides:
    - A custom manager that only returns completed tasks
    - Specialized methods for completed task operations
    - Different default ordering (by completion date)
    - Separate admin interface
    
    IMPORTANT: This does NOT create a new database table.
    It's just a different Python interface to the Task table.
    """
    
    # Custom manager that filters to completed tasks only
    objects = CompletedTaskManager()
    
    class Meta:
        proxy = True
        ordering = ['-completed_at']
        verbose_name = 'Completed Task'
        verbose_name_plural = 'Completed Tasks'
    
    def __str__(self):
        return f"{self.title} (Completed on {self.completed_at.strftime('%Y-%m-%d')})"
    
    def days_since_completion(self):
        """Calculate days since task was completed."""
        if self.completed_at:
            delta = timezone.now() - self.completed_at
            return delta.days
        return None
    
    def is_archivable(self, days=30):
        """
        Check if the task is old enough to be archived.
        
        Args:
            days: Number of days after completion to consider archivable
        
        Returns:
            bool: True if task was completed more than 'days' ago
        """
        days_since = self.days_since_completion()
        return days_since is not None and days_since > days
    
    def archive(self):
        """
        Archive the completed task (soft delete).
        
        This is a business operation specific to completed tasks.
        Only tasks completed more than 30 days ago can be archived.
        """
        if not self.is_archivable():
            raise ValueError("Task must be completed for at least 30 days before archiving")
        
        self.soft_delete()
    
    def get_completion_summary(self):
        """
        Get a summary of the task completion.
        
        Returns:
            dict: Summary information about the completed task
        """
        return {
            'title': self.title,
            'completed_at': self.completed_at,
            'days_since_completion': self.days_since_completion(),
            'completed_by': self.created_by.username if self.created_by else None,
            'priority': self.get_priority_display(),
            'was_overdue': self.due_date and self.completed_at > self.due_date if self.due_date else False,
        }
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure status is always 'completed'.
        
        This enforces the business rule that CompletedTask instances
        must always have status='completed'.
        """
        # Force status to completed
        self.status = Task.STATUS_COMPLETED
        
        # Ensure completed_at is set
        if not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)


"""
EXAMPLE USAGE:
==============

# Get all completed tasks (using proxy model)
completed = CompletedTask.objects.all()

# Get recently completed tasks (last 7 days)
recent = CompletedTask.objects.recent(days=7)

# Get archivable tasks (completed > 30 days ago)
archivable = CompletedTask.objects.archived()

# Archive old completed tasks
for task in CompletedTask.objects.archived():
    task.archive()

# Get completion summary
task = CompletedTask.objects.first()
summary = task.get_completion_summary()

# This is cleaner and more semantic than:
# Task.objects.filter(status='completed')
# And provides specialized methods that don't clutter the base Task model.

BENEFITS DEMONSTRATED:
======================

1. **No Table Duplication**: Same database table as Task
2. **Specialized Interface**: Only completed tasks, with completion-specific methods
3. **Query Optimization**: Manager pre-filters, reducing query complexity
4. **Semantic Clarity**: CompletedTask.objects.all() is clearer than Task.objects.filter(status='completed')
5. **Separation of Concerns**: Completion logic separate from general task logic
6. **Admin Flexibility**: Can have different admin interface for completed tasks
7. **API Design**: Clean endpoint separation (/api/tasks/ vs /api/completed-tasks/)
"""
