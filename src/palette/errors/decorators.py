"""
Error handling decorators for Palette.
Provides automatic error handling and retry logic.
"""

import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from datetime import datetime

from .base import PaletteError, GenerationError, IntegrationError
from .handlers import ErrorHandler, ConsoleErrorHandler


def handle_errors(
    handler: Optional[ErrorHandler] = None,
    fallback_return: Any = None,
    reraise: bool = True,
    error_types: Optional[List[Type[Exception]]] = None
):
    """
    Decorator to handle errors in functions.
    
    Args:
        handler: Error handler to use (defaults to ConsoleErrorHandler)
        fallback_return: Value to return on error (if reraise is False)
        reraise: Whether to reraise the error after handling
        error_types: Specific error types to handle (handles all if None)
    
    Example:
        @handle_errors(handler=ConsoleErrorHandler(verbose=True))
        def risky_function():
            # Function that might raise errors
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should handle this error type
                if error_types and not isinstance(e, tuple(error_types)):
                    raise
                
                # Use provided handler or default
                error_handler = handler or ConsoleErrorHandler()
                
                # Add context to Palette errors
                if isinstance(e, PaletteError):
                    e.add_context(
                        function=func.__name__,
                        module=func.__module__,
                        timestamp=datetime.now().isoformat()
                    )
                
                # Handle the error
                error_handler.handle(e)
                
                # Reraise or return fallback
                if reraise:
                    raise
                else:
                    return fallback_return
        
        return wrapper
    return decorator


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    error_types: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator to retry functions on specific errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        error_types: Error types that trigger retry (retries on all if None)
        on_retry: Optional callback called on each retry with (error, attempt)
    
    Example:
        @retry_on_error(max_attempts=3, delay=1.0, error_types=[IntegrationError])
        def api_call():
            # Function that might fail temporarily
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Check if we should retry this error type
                    if error_types and not isinstance(e, tuple(error_types)):
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        raise
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    # Sleep before retry
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # Should not reach here, but raise last error if we do
            raise last_error
        
        return wrapper
    return decorator


def convert_errors(
    error_mapping: Dict[Type[Exception], Type[PaletteError]],
    add_context: bool = True
):
    """
    Decorator to convert external errors to Palette errors.
    
    Args:
        error_mapping: Mapping from external error types to Palette error types
        add_context: Whether to add function context to converted errors
    
    Example:
        @convert_errors({
            requests.RequestException: IntegrationError,
            json.JSONDecodeError: GenerationError
        })
        def external_api_call():
            # Function that uses external libraries
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should convert this error
                for source_type, target_type in error_mapping.items():
                    if isinstance(e, source_type):
                        # Create new Palette error
                        palette_error = target_type(
                            message=str(e),
                            cause=e
                        )
                        
                        # Add context if requested
                        if add_context:
                            palette_error.add_context(
                                function=func.__name__,
                                module=func.__module__,
                                original_error=e.__class__.__name__
                            )
                        
                        raise palette_error
                
                # Re-raise if no conversion found
                raise
        
        return wrapper
    return decorator


def log_errors(
    logger_name: str = "palette",
    level: str = "ERROR",
    include_traceback: bool = True
):
    """
    Decorator to log errors using Python's logging module.
    
    Args:
        logger_name: Name of the logger to use
        level: Log level (ERROR, WARNING, etc.)
        include_traceback: Whether to include full traceback
    
    Example:
        @log_errors(logger_name="palette.generation")
        def generate_component():
            # Function that might fail
            pass
    """
    import logging
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Build log message
                message = f"Error in {func.__name__}: {str(e)}"
                
                # Add context for Palette errors
                if isinstance(e, PaletteError) and e.context:
                    message += f"\nContext: {e.context}"
                
                # Log at appropriate level
                log_method = getattr(logger, level.lower(), logger.error)
                log_method(message, exc_info=include_traceback)
                
                # Re-raise the error
                raise
        
        return wrapper
    return decorator


def timeout(seconds: int, error_message: str = "Function call timed out"):
    """
    Decorator to add timeout to functions (Unix-like systems only).
    
    Args:
        seconds: Timeout in seconds
        error_message: Error message for timeout
    
    Example:
        @timeout(30, "API call timed out")
        def slow_api_call():
            # Function that might take too long
            pass
    """
    import signal
    
    def decorator(func: Callable) -> Callable:
        def timeout_handler(signum, frame):
            raise GenerationError(error_message, context={"timeout_seconds": seconds})
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore previous handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator


def validate_result(
    validator: Callable[[Any], bool],
    error_message: str = "Result validation failed",
    error_type: Type[PaletteError] = PaletteError
):
    """
    Decorator to validate function results.
    
    Args:
        validator: Function that returns True if result is valid
        error_message: Error message for invalid results
        error_type: Error type to raise on validation failure
    
    Example:
        @validate_result(
            validator=lambda x: x is not None and len(x) > 0,
            error_message="Generated code is empty"
        )
        def generate_code():
            # Function that should return non-empty result
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if not validator(result):
                raise error_type(
                    error_message,
                    context={
                        "function": func.__name__,
                        "result_type": type(result).__name__
                    }
                )
            
            return result
        
        return wrapper
    return decorator


def cache_errors(
    cache_duration: int = 300,
    error_types: Optional[List[Type[Exception]]] = None
):
    """
    Decorator to cache errors to avoid repeated failures.
    Useful for external API calls that might be temporarily down.
    
    Args:
        cache_duration: How long to cache errors in seconds
        error_types: Error types to cache (caches all if None)
    
    Example:
        @cache_errors(cache_duration=60, error_types=[IntegrationError])
        def external_service_call():
            # Function that might fail due to external issues
            pass
    """
    # Error cache: (function_name, args_hash) -> (error, expiry_time)
    error_cache: Dict[Tuple[str, str], Tuple[Exception, float]] = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            import hashlib
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode()).hexdigest()
            cache_key = (func.__name__, args_hash)
            
            # Check cache
            current_time = time.time()
            if cache_key in error_cache:
                cached_error, expiry_time = error_cache[cache_key]
                if current_time < expiry_time:
                    # Re-raise cached error
                    raise cached_error
                else:
                    # Remove expired entry
                    del error_cache[cache_key]
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should cache this error
                if error_types and not isinstance(e, tuple(error_types)):
                    raise
                
                # Cache the error
                error_cache[cache_key] = (e, current_time + cache_duration)
                raise
        
        return wrapper
    return decorator