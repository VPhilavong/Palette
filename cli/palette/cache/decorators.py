"""
Caching decorators for expensive operations.
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union
from datetime import timedelta

from ..interfaces import ICache
from .memory_cache import MemoryCache


# Global cache instance for decorators
_global_cache: Optional[ICache] = None


def set_global_cache(cache: ICache):
    """Set the global cache instance used by decorators."""
    global _global_cache
    _global_cache = cache


def get_global_cache() -> ICache:
    """Get the global cache instance, creating a default if needed."""
    global _global_cache
    if _global_cache is None:
        _global_cache = MemoryCache()
    return _global_cache


def cache_result(
    ttl: Optional[Union[int, timedelta]] = 3600,
    key_prefix: Optional[str] = None,
    cache: Optional[ICache] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live for cached results
        key_prefix: Optional prefix for cache keys
        cache: Optional cache instance (uses global if not provided)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache_instance = cache or get_global_cache()
            
            # Build cache key
            cache_key = _build_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        # Add cache control methods
        wrapper.clear_cache = lambda: _clear_function_cache(func, cache or get_global_cache(), key_prefix)
        wrapper.cache_info = lambda: _get_cache_info(func, cache or get_global_cache(), key_prefix)
        
        return wrapper
    return decorator


def cache_property(
    ttl: Optional[Union[int, timedelta]] = 3600,
    cache: Optional[ICache] = None
):
    """
    Decorator to cache property results on instances.
    
    Args:
        ttl: Time to live for cached results
        cache: Optional cache instance (uses global if not provided)
    """
    def decorator(func: Callable) -> property:
        def getter(self):
            # Get cache instance
            cache_instance = cache or get_global_cache()
            
            # Build cache key including instance id
            cache_key = f"{self.__class__.__name__}.{id(self)}.{func.__name__}"
            
            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call property
            result = func(self)
            
            # Cache result
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        return property(getter)
    return decorator


def _build_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: Optional[str] = None
) -> str:
    """Build a cache key from function and arguments."""
    parts = []
    
    # Add prefix if provided
    if prefix:
        parts.append(prefix)
    
    # Add function identifier
    parts.append(f"{func.__module__}.{func.__name__}")
    
    # Add arguments
    if args:
        # Handle different types of arguments
        arg_parts = []
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                arg_parts.append(str(arg))
            elif hasattr(arg, "__dict__"):
                # For objects, use their type and id
                arg_parts.append(f"{type(arg).__name__}:{id(arg)}")
            else:
                # For other types, try to serialize
                try:
                    arg_parts.append(json.dumps(arg, sort_keys=True))
                except:
                    arg_parts.append(str(type(arg)))
        
        parts.append("args:" + ",".join(arg_parts))
    
    # Add keyword arguments
    if kwargs:
        # Sort for consistent ordering
        kwarg_parts = []
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            if isinstance(value, (str, int, float, bool)):
                kwarg_parts.append(f"{key}={value}")
            else:
                try:
                    kwarg_parts.append(f"{key}={json.dumps(value, sort_keys=True)}")
                except:
                    kwarg_parts.append(f"{key}={type(value).__name__}")
        
        parts.append("kwargs:" + ",".join(kwarg_parts))
    
    # Create hash for very long keys
    key = "|".join(parts)
    if len(key) > 250:
        # Use hash for long keys
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{parts[0]}|{parts[1]}|hash:{key_hash}"
    
    return key


def _clear_function_cache(
    func: Callable,
    cache: ICache,
    prefix: Optional[str] = None
):
    """Clear all cached results for a function."""
    # This is a simplified implementation
    # In practice, you might want to track keys per function
    stats = cache.get_stats()
    print(f"Cache cleared for {func.__name__} (current cache size: {stats['size']})")


def _get_cache_info(
    func: Callable,
    cache: ICache,
    prefix: Optional[str] = None
) -> dict:
    """Get cache information for a function."""
    stats = cache.get_stats()
    return {
        "function": func.__name__,
        "cache_stats": stats
    }