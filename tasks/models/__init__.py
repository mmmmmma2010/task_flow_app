"""
Models package initialization.

This module exports all models for easy importing.
"""

from .task import Task
from .proxy import CompletedTask
from .managers import TaskManager, CompletedTaskManager, TaskQuerySet

__all__ = [
    'Task',
    'CompletedTask',
    'TaskManager',
    'CompletedTaskManager',
    'TaskQuerySet',
]
