"""
Celery configuration for task_flow_app project.

This module initializes Celery and configures it to work with Django.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('task_flow_app')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Optional: Configure task routes
app.conf.task_routes = {
    'tasks.tasks.send_task_created_notification': {'queue': 'notifications'},
    'tasks.tasks.send_task_reminder': {'queue': 'notifications'},
    'tasks.tasks.cleanup_old_completed_tasks': {'queue': 'maintenance'},
}

# Optional: Configure task priorities
app.conf.task_default_priority = 5
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f'Request: {self.request!r}')
