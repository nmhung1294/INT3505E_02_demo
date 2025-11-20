"""
Logging configuration module using Python's built-in logging
Provides structured logging with JSON format and multiple handlers
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
            
        return json.dumps(log_data)


class SimpleFormatter(logging.Formatter):
    """
    Simple human-readable formatter for console output
    """
    def format(self, record):
        timestamp = datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname.ljust(8)
        message = record.getMessage()
        
        # Add extra context if available
        extras = []
        if hasattr(record, 'user_id'):
            extras.append(f"user={record.user_id}")
        if hasattr(record, 'endpoint'):
            extras.append(f"endpoint={record.endpoint}")
        if hasattr(record, 'duration'):
            extras.append(f"duration={record.duration}ms")
            
        extra_str = f" [{', '.join(extras)}]" if extras else ""
        
        return f"{timestamp} {level} {record.name}: {message}{extra_str}"


def setup_logging(app_name='book_management', log_level='INFO', log_dir='logs'):
    """
    Setup logging configuration with multiple handlers
    
    Args:
        app_name: Name of the application (used for log files)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console Handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SimpleFormatter())
    logger.addHandler(console_handler)
    
    # File Handler for all logs (JSON format)
    all_logs_file = log_path / f'{app_name}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        all_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error File Handler (only errors and above)
    error_logs_file = log_path / f'{app_name}_error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging initialized for {app_name}", extra={'log_level': log_level})
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance
    
    Args:
        name: Logger name (defaults to 'book_management')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name or 'book_management')


# Request logger helper
def log_request(logger, method, endpoint, status_code, duration_ms, user_id=None, ip_address=None):
    """
    Log HTTP request with structured data
    
    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user identifier
        ip_address: Optional client IP address
    """
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'duration': duration_ms,
    }
    
    if user_id:
        extra['user_id'] = user_id
    if ip_address:
        extra['ip_address'] = ip_address
    
    level = logging.INFO
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    
    logger.log(level, f"{method} {endpoint} - {status_code}", extra=extra)


# Database operation logger helper
def log_db_operation(logger, operation, table, record_id=None, success=True, error=None):
    """
    Log database operations
    
    Args:
        logger: Logger instance
        operation: Operation type (CREATE, READ, UPDATE, DELETE)
        table: Table/model name
        record_id: Optional record identifier
        success: Whether operation succeeded
        error: Optional error message
    """
    extra = {
        'operation': operation,
        'table': table,
    }
    
    if record_id:
        extra['record_id'] = record_id
    
    if success:
        msg = f"DB {operation} on {table}"
        if record_id:
            msg += f" (id={record_id})"
        logger.info(msg, extra=extra)
    else:
        msg = f"DB {operation} on {table} FAILED"
        if record_id:
            msg += f" (id={record_id})"
        if error:
            msg += f": {error}"
        logger.error(msg, extra=extra)


# Cache operation logger helper
def log_cache_operation(logger, operation, key, hit=None):
    """
    Log cache operations
    
    Args:
        logger: Logger instance
        operation: Operation type (GET, SET, DELETE)
        key: Cache key
        hit: For GET operations, whether it was a hit or miss
    """
    extra = {
        'operation': operation,
        'cache_key': key,
    }
    
    if hit is not None:
        extra['cache_hit'] = hit
    
    logger.debug(f"Cache {operation}: {key}", extra=extra)
