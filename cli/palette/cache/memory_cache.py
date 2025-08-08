"""
In-memory cache implementation.
"""

import time
from typing import Optional, Any, Union, Dict
from datetime import timedelta, datetime
from collections import OrderedDict
import threading

from ..interfaces import ICache


class CacheEntry:
    """A single cache entry with expiration."""
    
    def __init__(self, value: Any, ttl: Optional[Union[int, timedelta]] = None):
        self.value = value
        self.created_at = datetime.now()
        
        if ttl is None:
            self.expires_at = None
        elif isinstance(ttl, timedelta):
            self.expires_at = self.created_at + ttl
        else:
            # ttl is in seconds
            self.expires_at = self.created_at + timedelta(seconds=ttl)
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class MemoryCache(ICache):
    """
    Thread-safe in-memory cache with TTL support.
    Uses LRU eviction when size limit is reached.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a value in the cache."""
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create entry
            entry = CacheEntry(value, ttl)
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # Check size limit
                if len(self._cache) >= self.max_size:
                    # Evict oldest (first) entry
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._evictions += 1
                
                self._cache[key] = entry
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            return True
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns number of entries removed."""
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)