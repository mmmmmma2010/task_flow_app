"""
Django Signals for Task model.

Signals provide a way to execute code when certain events occur.
We use signals sparingly, preferring Celery tasks for heavy operations.

SIGNALS vs CELERY:
==================

Use Signals when:
- Operation is fast and synchronous
- Operation is critical to data integrity
- Operation must happen before/after save

Use Celery when:
- Operation is slow (emails, API calls)
- Operation can fail and needs retry
- Operation should not block the request

In this project, we primarily use Celery for async operations,
but signals are shown here for demonstration purposes.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from tasks.models import Task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Task post-save.
    
    This demonstrates signal usage, but note that we prefer
    using the service layer + Celery for most operations.
    
    Args:
        sender: The model class (Task)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(f"Signal: New task created - {instance.id}: {instance.title}")
        
        # Example: Could update a counter cache
        # In production, this might update a dashboard cache
        cache_key = f'user_task_count:{instance.created_by.id}'
        cache.delete(cache_key)
    else:
        logger.debug(f"Signal: Task updated - {instance.id}: {instance.title}")
        
        # Invalidate task cache
        cache_key = f'task:{instance.id}'
        cache.delete(cache_key)


@receiver(pre_delete, sender=Task)
def task_pre_delete(sender, instance, **kwargs):
    """
    Signal handler for Task pre-delete.
    
    This is called before a task is deleted (hard delete).
    Since we use soft deletes, this rarely happens.
    
    Args:
        sender: The model class (Task)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    logger.warning(f"Signal: Task being hard deleted - {instance.id}: {instance.title}")
    
    # Could log to audit trail
    # Could notify admins
    # Could backup data


# Example of a custom signal (not used in this project, but shown for reference)
# from django.dispatch import Signal
# 
# task_completed = Signal()
# 
# @receiver(task_completed)
# def handle_task_completed(sender, task, **kwargs):
#     """Handle custom task_completed signal."""
#     logger.info(f"Custom signal: Task completed - {task.id}")
