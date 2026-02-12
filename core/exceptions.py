"""
Custom exception handler and exception classes.
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that logs errors and provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    if response is not None:
        logger.error(
            f"API Exception: {exc.__class__.__name__} - {str(exc)}",
            extra={'context': context}
        )
    else:
        # If response is None, it's an unhandled exception
        logger.exception(
            f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)}",
            extra={'context': context}
        )
    
    # Customize the response format
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': str(exc),
            'details': response.data
        }
        response.data = custom_response_data
    
    return response


class TaskNotFoundError(APIException):
    """Exception raised when a task is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Task not found.'
    default_code = 'task_not_found'


class TaskAlreadyCompletedError(APIException):
    """Exception raised when trying to complete an already completed task."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Task is already completed.'
    default_code = 'task_already_completed'


class InvalidTaskStatusError(APIException):
    """Exception raised when an invalid task status is provided."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid task status.'
    default_code = 'invalid_task_status'


class ServiceError(APIException):
    """Generic service layer error."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A service error occurred.'
    default_code = 'service_error'
