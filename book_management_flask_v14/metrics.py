"""
Prometheus metrics collector for monitoring
Tracks HTTP requests, database operations, cache performance, and system metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from flask import request, g


# ==========================================
# HTTP Metrics
# ==========================================

# Counter for total HTTP requests
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogram for request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Counter for HTTP errors
http_errors_total = Counter(
    'http_errors_total',
    'Total number of HTTP errors',
    ['method', 'endpoint', 'status']
)

# Gauge for active requests
http_requests_active = Gauge(
    'http_requests_active',
    'Number of requests currently being processed'
)


# ==========================================
# Database Metrics
# ==========================================

# Counter for database operations
db_operations_total = Counter(
    'db_operations_total',
    'Total number of database operations',
    ['operation', 'table', 'status']
)

# Histogram for database operation duration
db_operation_duration_seconds = Histogram(
    'db_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Counter for database errors
db_errors_total = Counter(
    'db_errors_total',
    'Total number of database errors',
    ['operation', 'table']
)


# ==========================================
# Cache Metrics
# ==========================================

# Counter for cache operations
cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation', 'status']
)

# Cache hit rate
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses'
)

# Gauge for cache size
cache_size = Gauge(
    'cache_size_bytes',
    'Current size of cache in bytes'
)

cache_entries = Gauge(
    'cache_entries_total',
    'Current number of entries in cache'
)


# ==========================================
# Business Metrics
# ==========================================

# Counter for books borrowed
books_borrowed_total = Counter(
    'books_borrowed_total',
    'Total number of books borrowed'
)

# Counter for books returned
books_returned_total = Counter(
    'books_returned_total',
    'Total number of books returned'
)

# Gauge for active borrowings
active_borrowings = Gauge(
    'active_borrowings_total',
    'Current number of active borrowings'
)

# Counter for user registrations
user_registrations_total = Counter(
    'user_registrations_total',
    'Total number of user registrations'
)

# Counter for authentication attempts
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['status']
)


# ==========================================
# Application Info
# ==========================================

app_info = Info(
    'book_management_app',
    'Book Management Application Information'
)


# ==========================================
# Helper Functions
# ==========================================

def track_request():
    """
    Middleware to track HTTP request metrics
    Should be called at the beginning of request processing
    """
    g.start_time = time.time()
    http_requests_active.inc()


def finalize_request_metrics(response):
    """
    Middleware to finalize HTTP request metrics
    Should be called at the end of request processing
    
    Args:
        response: Flask response object
    
    Returns:
        response object (unchanged)
    """
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        
        method = request.method
        endpoint = request.endpoint or 'unknown'
        status = response.status_code
        
        # Record metrics
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint, status=status).observe(duration)
        
        # Track errors
        if status >= 400:
            http_errors_total.labels(method=method, endpoint=endpoint, status=status).inc()
        
        http_requests_active.dec()
    
    return response


def track_db_operation(operation, table):
    """
    Decorator to track database operation metrics
    
    Args:
        operation: Operation type (e.g., 'SELECT', 'INSERT', 'UPDATE', 'DELETE')
        table: Table/model name
    
    Example:
        @track_db_operation('SELECT', 'book_title')
        def get_book(book_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                db_errors_total.labels(operation=operation, table=table).inc()
                raise
            finally:
                duration = time.time() - start_time
                db_operations_total.labels(operation=operation, table=table, status=status).inc()
                db_operation_duration_seconds.labels(operation=operation, table=table).observe(duration)
        
        return wrapper
    return decorator


def record_cache_hit():
    """Record a cache hit"""
    cache_hits_total.inc()
    cache_operations_total.labels(operation='get', status='hit').inc()


def record_cache_miss():
    """Record a cache miss"""
    cache_misses_total.inc()
    cache_operations_total.labels(operation='get', status='miss').inc()


def record_cache_set():
    """Record a cache set operation"""
    cache_operations_total.labels(operation='set', status='success').inc()


def record_cache_delete():
    """Record a cache delete operation"""
    cache_operations_total.labels(operation='delete', status='success').inc()


def update_cache_size(size_bytes, num_entries):
    """
    Update cache size metrics
    
    Args:
        size_bytes: Total size of cache in bytes
        num_entries: Number of entries in cache
    """
    cache_size.set(size_bytes)
    cache_entries.set(num_entries)


def record_book_borrowed():
    """Record a book borrowing"""
    books_borrowed_total.inc()


def record_book_returned():
    """Record a book return"""
    books_returned_total.inc()


def update_active_borrowings(count):
    """
    Update active borrowings gauge
    
    Args:
        count: Current number of active borrowings
    """
    active_borrowings.set(count)


def record_user_registration():
    """Record a new user registration"""
    user_registrations_total.inc()


def record_auth_attempt(success):
    """
    Record an authentication attempt
    
    Args:
        success: Whether authentication was successful
    """
    status = 'success' if success else 'failure'
    auth_attempts_total.labels(status=status).inc()


def get_cache_hit_rate():
    """
    Calculate cache hit rate
    
    Returns:
        Hit rate as a percentage (0-100) or None if no data
    """
    hits = cache_hits_total._value.get()
    misses = cache_misses_total._value.get()
    total = hits + misses
    
    if total == 0:
        return None
    
    return (hits / total) * 100


def initialize_app_info(version='1.3', environment='development'):
    """
    Initialize application info metrics
    
    Args:
        version: Application version
        environment: Deployment environment
    """
    app_info.info({
        'version': version,
        'environment': environment,
        'application': 'book_management_api'
    })


def get_metrics():
    """
    Get all metrics in Prometheus format
    
    Returns:
        Metrics data as bytes
    """
    return generate_latest()


def get_metrics_content_type():
    """
    Get the content type for metrics endpoint
    
    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
