"""
Health check endpoint for Render.com and monitoring.
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint that verifies:
    - Application is running
    - Database connectivity
    - Redis connectivity
    
    Returns 200 OK if healthy, 503 Service Unavailable if not.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis connection
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        
        if cache_value != 'ok':
            raise Exception("Redis cache test failed")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
