"""
Task model - Base model for task management.

This module defines the core Task model with all necessary fields,
validation, and business logic.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from .managers import TaskManager

User = get_user_model()


class Task(models.Model):
    """
    Task model representing a single task in the system.
    
    This is the base model that stores all task data. The CompletedTask
    proxy model provides a different interface to this same data.
    
    Fields:
        - title: Task title (required)
        - description: Detailed task description
        - status: Current task status (pending, in_progress, completed)
        - priority: Task priority level (low, medium, high)
        - due_date: When the task should be completed
        - created_by: User who created the task
        - assigned_to: User assigned to complete the task
        - completed_at: Timestamp when task was marked complete
        - is_deleted: Soft delete flag
        - deleted_at: Timestamp when task was soft deleted
        - created_at: Timestamp when task was created
        - updated_at: Timestamp when task was last updated
    """
    
    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    
    # Priority choices
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]
    
    # Core fields
    title = models.CharField(
        max_length=255,
        help_text="Task title"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the task"
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text="Current status of the task"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
        help_text="Priority level of the task"
    )
    
    # Dates
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the task should be completed"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was marked as completed"
    )
    
    # User relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        help_text="User who created this task"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text="User assigned to complete this task"
    )
    
    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was soft deleted"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the task was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the task was last updated"
    )
    
    # Custom manager
    objects = TaskManager()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def clean(self):
        """Validate the model before saving."""
        super().clean()
        
        # Validate that completed tasks have a completed_at timestamp
        if self.status == self.STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Validate that due_date is in the future for new tasks
        if not self.pk and self.due_date and self.due_date < timezone.now():
            raise ValidationError({
                'due_date': 'Due date cannot be in the past for new tasks.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to perform validation and set timestamps."""
        # Run validation
        self.full_clean()
        
        # Set completed_at when status changes to completed
        if self.status == self.STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Set deleted_at when soft deleting
        if self.is_deleted and not self.deleted_at:
            self.deleted_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def mark_complete(self):
        """Mark the task as completed."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def soft_delete(self):
        """Soft delete the task."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted task."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if self.due_date and self.status != self.STATUS_COMPLETED:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Calculate days until due date."""
        if self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None
