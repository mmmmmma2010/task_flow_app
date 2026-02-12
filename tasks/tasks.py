"""
Celery Tasks for asynchronous operations.

This module contains all Celery tasks for background processing.
Tasks are triggered by the service layer or scheduled via Celery Beat.

WHY CELERY?
===========

Celery provides:
1. **Non-blocking Operations**: API responds immediately, task runs in background
2. **Retry Logic**: Failed tasks can automatically retry
3. **Scheduling**: Periodic tasks (cleanup, reminders, reports)
4. **Scalability**: Add more workers to handle increased load
5. **Monitoring**: Track task status and performance

CELERY vs SIGNALS:
==================

Use Celery when:
- Operation is time-consuming (sending emails, API calls)
- Operation can fail and needs retry logic
- Operation should not block the HTTP response
- Operation needs to be scheduled

Use Signals when:
- Operation is fast and must happen synchronously
- Operation is critical to data integrity
- Operation is simple model-level logic
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_created_notification(self, task_id: int):
    """
    Send email notification when a task is created.
    
    This task is triggered by TaskService.create_task() and runs asynchronously.
    If it fails, it will retry up to 3 times with 60 second delays.
    
    Args:
        task_id: ID of the created task
    
    Returns:
        dict: Status of the email sending operation
    """
    try:
        # Import here to avoid circular imports
        from tasks.models import Task
        
        # Get the task
        task = Task.objects.get(id=task_id)
        
        # Prepare email
        subject = f'New Task Created: {task.title}'
        message = f"""
        A new task has been created:
        
        Title: {task.title}
        Description: {task.description}
        Priority: {task.get_priority_display()}
        Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'Not set'}
        Created By: {task.created_by.username}
        Assigned To: {task.assigned_to.username if task.assigned_to else 'Unassigned'}
        
        Status: {task.get_status_display()}
        
        Please log in to view more details.
        """
        
        # Determine recipients
        recipients = [task.created_by.email]
        if task.assigned_to and task.assigned_to.email:
            recipients.append(task.assigned_to.email)
        
        # Remove duplicates and empty emails
        recipients = list(set(filter(None, recipients)))
        
        if not recipients:
            logger.warning(f"No email recipients for task {task_id}")
            return {'status': 'skipped', 'reason': 'no_recipients'}
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        
        logger.info(f"Task creation notification sent for task {task_id} to {recipients}")
        
        return {
            'status': 'sent',
            'task_id': task_id,
            'recipients': recipients,
        }
        
    except Exception as exc:
        logger.error(f"Error sending task notification for task {task_id}: {str(exc)}")
        
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_reminder(self, task_id: int):
    """
    Send reminder email for tasks approaching due date.
    
    This task can be scheduled via Celery Beat or triggered manually.
    
    Args:
        task_id: ID of the task to send reminder for
    
    Returns:
        dict: Status of the reminder sending operation
    """
    try:
        from tasks.models import Task
        
        task = Task.objects.active().get(id=task_id)
        
        # Only send reminder for non-completed tasks
        if task.status == Task.STATUS_COMPLETED:
            return {'status': 'skipped', 'reason': 'task_completed'}
        
        # Check if task is due soon (within 24 hours)
        if task.due_date:
            time_until_due = task.due_date - timezone.now()
            hours_until_due = time_until_due.total_seconds() / 3600
            
            if hours_until_due < 0:
                urgency = "OVERDUE"
            elif hours_until_due < 24:
                urgency = "DUE SOON"
            else:
                return {'status': 'skipped', 'reason': 'not_urgent'}
        else:
            return {'status': 'skipped', 'reason': 'no_due_date'}
        
        # Prepare reminder email
        subject = f'Task Reminder: {task.title} - {urgency}'
        message = f"""
        This is a reminder about your task:
        
        Title: {task.title}
        Description: {task.description}
        Priority: {task.get_priority_display()}
        Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}
        Status: {urgency}
        
        Please complete this task as soon as possible.
        """
        
        # Send to assigned user or creator
        recipient = task.assigned_to.email if task.assigned_to else task.created_by.email
        
        if not recipient:
            return {'status': 'skipped', 'reason': 'no_recipient'}
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        
        logger.info(f"Task reminder sent for task {task_id} to {recipient}")
        
        return {
            'status': 'sent',
            'task_id': task_id,
            'recipient': recipient,
            'urgency': urgency,
        }
        
    except Exception as exc:
        logger.error(f"Error sending task reminder for task {task_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_completed_tasks():
    """
    Periodic task to archive old completed tasks.
    
    This task is scheduled via Celery Beat to run daily.
    It archives completed tasks older than 30 days.
    
    Returns:
        dict: Summary of cleanup operation
    """
    try:
        from tasks.services import CompletedTaskService
        
        logger.info("Starting cleanup of old completed tasks")
        
        # Archive tasks completed more than 30 days ago
        archived_count = CompletedTaskService.archive_old_tasks(days=30)
        
        logger.info(f"Cleanup complete: {archived_count} tasks archived")
        
        return {
            'status': 'completed',
            'archived_count': archived_count,
            'timestamp': timezone.now().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Error during cleanup: {str(exc)}")
        return {
            'status': 'failed',
            'error': str(exc),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task
def send_daily_task_summary():
    """
    Send daily summary of tasks to all users.
    
    This is an example of a scheduled task that runs daily
    to send task summaries to users.
    
    Returns:
        dict: Summary of emails sent
    """
    try:
        from django.contrib.auth import get_user_model
        from tasks.services import TaskService
        
        User = get_user_model()
        users = User.objects.filter(is_active=True)
        
        sent_count = 0
        
        for user in users:
            if not user.email:
                continue
            
            # Get user's task statistics
            stats = TaskService.get_task_statistics(user)
            
            # Only send if user has active tasks
            if stats['total'] == 0:
                continue
            
            subject = f'Daily Task Summary - {timezone.now().strftime("%Y-%m-%d")}'
            message = f"""
            Hello {user.username},
            
            Here's your daily task summary:
            
            Total Tasks: {stats['total']}
            Pending: {stats['pending']}
            In Progress: {stats['in_progress']}
            Completed: {stats['completed']}
            Overdue: {stats['overdue']}
            High Priority: {stats['high_priority']}
            
            Have a productive day!
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            
            sent_count += 1
        
        logger.info(f"Daily summary sent to {sent_count} users")
        
        return {
            'status': 'completed',
            'emails_sent': sent_count,
            'timestamp': timezone.now().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Error sending daily summaries: {str(exc)}")
        return {
            'status': 'failed',
            'error': str(exc),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task
def check_overdue_tasks():
    """
    Check for overdue tasks and send reminders.
    
    This task runs periodically to identify overdue tasks
    and trigger reminder emails.
    
    Returns:
        dict: Summary of reminders sent
    """
    try:
        from tasks.services import TaskService
        
        overdue_tasks = TaskService.get_overdue_tasks(use_cache=False)
        
        reminder_count = 0
        
        for task in overdue_tasks:
            # Trigger reminder task
            send_task_reminder.delay(task.id)
            reminder_count += 1
        
        logger.info(f"Triggered {reminder_count} overdue task reminders")
        
        return {
            'status': 'completed',
            'reminders_triggered': reminder_count,
            'timestamp': timezone.now().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Error checking overdue tasks: {str(exc)}")
        return {
            'status': 'failed',
            'error': str(exc),
            'timestamp': timezone.now().isoformat(),
        }
