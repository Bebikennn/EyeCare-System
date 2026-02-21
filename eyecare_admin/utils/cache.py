"""
Caching utilities for performance optimization
"""
from functools import wraps
from flask import request
import hashlib
import json
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache implementation with TTL and pattern-based invalidation"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}  # Track cache hits for monitoring
    
    def get(self, key):
        """Get value from cache"""
        if key in self._cache:
            # Check if expired
            if key in self._timestamps:
                if datetime.now(timezone.utc) > self._timestamps[key]:
                    self.delete(key)
                    return None
            # Track access
            self._access_count[key] = self._access_count.get(key, 0) + 1
            return self._cache[key]
        return None
    
    def set(self, key, value, timeout=300):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Timeout in seconds (default 5 minutes)
        """
        self._cache[key] = value
        if timeout:
            self._timestamps[key] = datetime.now(timezone.utc) + timedelta(seconds=timeout)
        self._access_count[key] = 0
        logger.debug(f"Cache SET: {key} (timeout={timeout}s)")
    
    def delete(self, key):
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        if key in self._access_count:
            del self._access_count[key]
        logger.debug(f"Cache DELETE: {key}")
    
    def clear(self):
        """Clear entire cache"""
        count = len(self._cache)
        self._cache.clear()
        self._timestamps.clear()
        self._access_count.clear()
        logger.info(f"Cache CLEAR: removed {count} entries")
    
    def clear_expired(self):
        """Clear all expired entries"""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if now > timestamp
        ]
        for key in expired_keys:
            self.delete(key)
        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        return len(expired_keys)
    
    def get_stats(self):
        """Get cache statistics"""
        total_entries = len(self._cache)
        total_hits = sum(self._access_count.values())
        hot_keys = sorted(
            self._access_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'hot_keys': [{'key': k, 'hits': v} for k, v in hot_keys],
            'memory_estimate_kb': total_entries * 1  # Rough estimate
        }


# Global cache instance
cache = SimpleCache()


def cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    key_data = {
        'args': args,
        'kwargs': kwargs,
        'path': request.path if request else None,
        'query': request.args.to_dict(flat=False) if request else None,
        'method': request.method if request else None,
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(timeout=300, key_prefix='view'):
    """
    Decorator to cache function results
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = f(*args, **kwargs)
            cache.set(key, result, timeout)
            return result
        
        return decorated_function
    return decorator


def invalidate_cache(key_prefix=None):
    """
    Invalidate cache entries
    
    Args:
        key_prefix: Prefix to match (None = clear all)
    
    Examples:
        invalidate_cache('user_stats')  # Clear all user_stats:* keys
        invalidate_cache()  # Clear entire cache
    """
    if key_prefix is None:
        cache.clear()
    else:
        # Clear entries matching prefix
        keys_to_delete = [k for k in cache._cache.keys() if k.startswith(key_prefix)]
        for key in keys_to_delete:
            cache.delete(key)
        logger.info(f"Cache invalidation: removed {len(keys_to_delete)} entries matching '{key_prefix}*'")
        return len(keys_to_delete)


def get_cache_stats():
    """Get cache statistics for monitoring"""
    return cache.get_stats()
