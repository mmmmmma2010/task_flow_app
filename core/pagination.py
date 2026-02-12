"""
Custom pagination classes for the API.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with configurable page size.
    
    Default: 20 items per page
    Max: 100 items per page
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for large result sets.
    
    Default: 50 items per page
    Max: 200 items per page
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
