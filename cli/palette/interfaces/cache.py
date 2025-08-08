"""
Cache interface for expensive operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Union
from datetime import timedelta


class ICache(ABC):
    """
    Abstract interface for caching implementations.
    Used to cache expensive operations like AST parsing and API calls.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)
            
        Returns:
            True if successfully cached
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was deleted
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            True if cache was cleared
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key exists and hasn't expired
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics (hits, misses, size, etc.)
        """
        pass