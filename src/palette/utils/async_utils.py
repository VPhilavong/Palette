"""
Async-safe utilities for mixing sync and async code.
Solves event loop conflicts when calling asyncio.run() within running loops.
"""

import asyncio
import functools
import threading
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor


T = TypeVar('T')


def is_running_in_event_loop() -> bool:
    """Check if code is running within an asyncio event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def safe_run_async(coro: Awaitable[T]) -> T:
    """
    Safely run async code from both sync and async contexts.
    
    - If no event loop is running: uses asyncio.run()
    - If event loop is running: creates new thread with new loop
    
    Args:
        coro: Coroutine to execute
        
    Returns:
        Result of the coroutine execution
    """
    if not is_running_in_event_loop():
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # Event loop is running, use thread pool to avoid conflicts
        return _run_in_thread(coro)


def _run_in_thread(coro: Awaitable[T]) -> T:
    """Run coroutine in a separate thread with its own event loop."""
    result = None
    exception = None
    
    def _run_in_new_loop():
        nonlocal result, exception
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            exception = e
    
    # Run in thread pool
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_in_new_loop)
        future.result()  # Wait for completion
    
    if exception:
        raise exception
    return result


class AsyncSafeRunner:
    """
    Reusable class for running async functions safely from sync contexts.
    
    Usage:
        runner = AsyncSafeRunner()
        result = runner.run(some_async_function(args))
    """
    
    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout
        self._thread_pool: Optional[ThreadPoolExecutor] = None
    
    def run(self, coro: Awaitable[T]) -> T:
        """Run coroutine safely, handling event loop conflicts."""
        return safe_run_async(coro)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)


def async_to_sync(async_func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    """
    Decorator to convert async functions to sync functions with safe execution.
    
    Usage:
        @async_to_sync
        async def my_async_function(arg1, arg2):
            await some_async_operation()
            return result
        
        # Can now be called synchronously
        result = my_async_function(arg1, arg2)
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        coro = async_func(*args, **kwargs)
        return safe_run_async(coro)
    
    return wrapper


class AsyncCompatible:
    """
    Mixin class to add async-safe execution capabilities to any class.
    
    Usage:
        class MyClass(AsyncCompatible):
            async def async_method(self):
                await some_operation()
                return result
            
            def sync_method(self):
                # Can safely call async methods
                return self.run_async(self.async_method())
    """
    
    def run_async(self, coro: Awaitable[T]) -> T:
        """Run async code safely from this class."""
        return safe_run_async(coro)


def get_event_loop_info() -> dict:
    """
    Get detailed information about the current event loop state.
    Useful for debugging async issues.
    """
    info = {
        "has_running_loop": False,
        "loop_is_running": False,
        "thread_name": threading.current_thread().name,
        "thread_id": threading.get_ident(),
    }
    
    try:
        loop = asyncio.get_running_loop()
        info["has_running_loop"] = True
        info["loop_is_running"] = loop.is_running()
        info["loop_debug"] = loop.get_debug()
    except RuntimeError as e:
        info["error"] = str(e)
    
    return info


# Convenience functions for common patterns
def run_async_safe(coro: Awaitable[T]) -> T:
    """Alias for safe_run_async for better readability."""
    return safe_run_async(coro)


def make_sync(async_func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    """Alias for async_to_sync decorator."""
    return async_to_sync(async_func)