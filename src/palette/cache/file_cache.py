"""
File-based cache implementation for persistent caching.
"""

import os
import json
import pickle
import hashlib
import time
from typing import Optional, Any, Union, Dict
from datetime import timedelta, datetime
from pathlib import Path
import threading

from ..interfaces import ICache


class FileCache(ICache):
    """
    File-based cache for persistent storage across sessions.
    Useful for caching expensive operations like AST parsing.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None, 
        default_ttl: Optional[int] = 3600,
        serializer: str = "pickle"  # "pickle" or "json"
    ):
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.palette/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.serializer = serializer
        self._lock = threading.RLock()
        
        # Metadata file for tracking cache entries
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._metadata = self._load_metadata()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            # Check metadata first
            if key not in self._metadata:
                return None
            
            entry_meta = self._metadata[key]
            
            # Check expiration
            if self._is_expired(entry_meta):
                self.delete(key)
                return None
            
            # Load value from file
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                # Metadata inconsistency, clean up
                del self._metadata[key]
                self._save_metadata()
                return None
            
            try:
                value = self._load_value(cache_file)
                
                # Update access time
                entry_meta["last_accessed"] = datetime.now().isoformat()
                self._save_metadata()
                
                return value
            except Exception as e:
                print(f"Cache read error for {key}: {e}")
                self.delete(key)
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a value in the cache."""
        with self._lock:
            try:
                # Use default TTL if not specified
                if ttl is None:
                    ttl = self.default_ttl
                
                # Calculate expiration
                if ttl is None:
                    expires_at = None
                elif isinstance(ttl, timedelta):
                    expires_at = (datetime.now() + ttl).isoformat()
                else:
                    expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
                
                # Save value to file
                cache_file = self._get_cache_file(key)
                self._save_value(cache_file, value)
                
                # Update metadata
                self._metadata[key] = {
                    "created_at": datetime.now().isoformat(),
                    "expires_at": expires_at,
                    "last_accessed": datetime.now().isoformat(),
                    "file": cache_file.name,
                    "size": cache_file.stat().st_size
                }
                self._save_metadata()
                
                return True
                
            except Exception as e:
                print(f"Cache write error for {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        with self._lock:
            if key not in self._metadata:
                return False
            
            # Remove file
            cache_file = self._get_cache_file(key)
            try:
                if cache_file.exists():
                    cache_file.unlink()
            except Exception as e:
                print(f"Error deleting cache file: {e}")
            
            # Remove from metadata
            del self._metadata[key]
            self._save_metadata()
            
            return True
    
    def clear(self) -> bool:
        """Clear all cached values."""
        with self._lock:
            # Remove all cache files
            for key in list(self._metadata.keys()):
                self.delete(key)
            
            # Clear metadata
            self._metadata = {}
            self._save_metadata()
            
            return True
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            if key not in self._metadata:
                return False
            
            entry_meta = self._metadata[key]
            if self._is_expired(entry_meta):
                self.delete(key)
                return False
            
            # Check if file actually exists
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                del self._metadata[key]
                self._save_metadata()
                return False
            
            return True
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(
                entry.get("size", 0) 
                for entry in self._metadata.values()
            )
            
            # Count expired entries
            expired_count = sum(
                1 for entry in self._metadata.values()
                if self._is_expired(entry)
            )
            
            return {
                "size": len(self._metadata),
                "expired_entries": expired_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "cache_dir": str(self.cache_dir)
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns number of entries removed."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._metadata.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                self.delete(key)
            
            return len(expired_keys)
    
    def _get_cache_file(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        extension = ".pkl" if self.serializer == "pickle" else ".json"
        return self.cache_dir / f"{key_hash}{extension}"
    
    def _load_value(self, cache_file: Path) -> Any:
        """Load value from cache file."""
        if self.serializer == "pickle":
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        else:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    
    def _save_value(self, cache_file: Path, value: Any):
        """Save value to cache file."""
        if self.serializer == "pickle":
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)
        else:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load metadata from file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")
    
    def _is_expired(self, entry_meta: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        expires_at = entry_meta.get("expires_at")
        if expires_at is None:
            return False
        
        try:
            expiration = datetime.fromisoformat(expires_at)
            return datetime.now() > expiration
        except Exception:
            return True