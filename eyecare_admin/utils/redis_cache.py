"""
Redis Cache Implementation
Replaces in-memory caching with Redis for production scalability
"""
from functools import wraps
import json
import hashlib
import time
from datetime import timedelta

# Try to import Redis, fallback to in-memory if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis-py not installed. Install with: pip install redis")

# Simple in-memory cache fallback
class SimpleCache:
    """Simple in-memory cache (fallback when Redis unavailable)"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        if key in self._cache:
            value, expires_at = self._cache[key]
            if expires_at is None or expires_at > time.time():
                # For in-memory cache, value is already a Python object
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key, value, timeout=None):
        expires_at = (time.time() + timeout) if timeout else None
        self._cache[key] = (value, expires_at)
        return True
    
    def setex(self, key, timeout, value):
        """Redis-compatible setex"""
        return self.set(key, value, timeout)
    
    def delete(self, key, *keys):
        """Delete one or more keys"""
        deleted = 0
        for k in (key,) + keys:
            if k in self._cache:
                del self._cache[k]
                deleted += 1
        return deleted
    
    def flushdb(self):
        """Clear entire database"""
        self._cache.clear()
        return True
    
    def exists(self, key):
        """Check if key exists and not expired"""
        if key in self._cache:
            _, expires_at = self._cache[key]
            if expires_at is None or expires_at > time.time():
                return 1
            else:
                del self._cache[key]
        return 0
    
    def ttl(self, key):
        """Get time to live for key"""
        if key in self._cache:
            _, expires_at = self._cache[key]
            if expires_at is None:
                return -1  # No expiration
            ttl = int(expires_at - time.time())
            return ttl if ttl > 0 else -2  # -2 means expired
        return -2  # Key doesn't exist
    
    def keys(self, pattern='*'):
        """Get keys matching pattern"""
        if pattern == '*':
            return list(self._cache.keys())
        else:
            pattern = pattern.replace('*', '')
            return [k for k in self._cache.keys() if pattern in k]
    
    def dbsize(self):
        """Get number of keys"""
        return len(self._cache)
    
    def info(self, section=None):
        """Get info (stub for compatibility)"""
        return {
            'keyspace_hits': 0,
            'keyspace_misses': 0,
            'used_memory_human': 'N/A'
        }


class RedisCache:
    """Redis-based cache for production use"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """Initialize Redis connection with fallback"""
        self.redis_client = False
        
        if not REDIS_AVAILABLE:
            print("⚠ redis-py not installed. Using in-memory cache fallback.")
            self.client = SimpleCache()
            return
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            self.client.ping()
            self.redis_client = True
            print(f"✓ Redis connected: {host}:{port}")
        except Exception as e:
            print(f"⚠ Redis not available ({e.__class__.__name__}). Using in-memory cache fallback.")
            self.client = SimpleCache()
            self.redis_client = False
    
    def get(self, key):
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, timeout=300):
        """Set value in cache with timeout (seconds)"""
        try:
            serialized = json.dumps(value, default=str)
            if timeout:
                self.client.setex(key, timeout, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear(self):
        """Clear all cache"""
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False
    
    def exists(self, key):
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def get_ttl(self, key):
        """Get time to live for key"""
        try:
            if self.redis_client:
                return self.client.ttl(key)
            else:
                return self.client.ttl(key)
        except Exception as e:
            print(f"Redis ttl error: {e}")
            return -1
    
    def invalidate_by_prefix(self, prefix):
        """Invalidate all keys with given prefix"""
        try:
            pattern = f"{prefix}*"
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys) if self.redis_client else sum(self.client.delete(k) for k in keys)
                return deleted
            return 0
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return 0
    
    def get_stats(self):
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.client.info('stats')
                memory = self.client.info('memory')
                return {
                    'type': 'redis',
                    'keys': self.client.dbsize(),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'memory_used_bytes': memory.get('used_memory', 0),
                    'memory_used_human': memory.get('used_memory_human', 'N/A')
                }
            else:
                return {
                    'type': 'in-memory',
                    'keys': self.client.dbsize()
                }
        except Exception as e:
            return {'error': str(e)}

# Global cache instance
_cache_instance = None

def get_cache():
    """Get or create cache instance"""
    global _cache_instance
    
    if _cache_instance is None:
        # Try to use Redis
        if REDIS_AVAILABLE:
            try:
                import os
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', 6379))
                redis_password = os.getenv('REDIS_PASSWORD', None)
                
                _cache_instance = RedisCache(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password
                )
                return _cache_instance
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                print("Falling back to in-memory cache")
        
        # Fallback to in-memory cache
        from utils.cache import SimpleCache
        _cache_instance = SimpleCache()
    
    return _cache_instance

def cached(timeout=300, key_prefix=''):
    """
    Decorator to cache function results
    
    Args:
        timeout: Cache timeout in seconds (default 300 = 5 minutes)
        key_prefix: Prefix for cache key
    
    Usage:
        @cached(timeout=600, key_prefix='user_stats')
        def get_user_stats():
            return expensive_operation()
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = _build_cache_key(f, key_prefix, args, kwargs)
            
            # Try to get from cache
            cache = get_cache()
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator

def _build_cache_key(func, prefix, args, kwargs):
    """Build a unique cache key for function call"""
    # Include function name
    key_parts = [func.__module__, func.__name__]
    
    # Add prefix if provided
    if prefix:
        key_parts.insert(0, prefix)
    
    # Add args and kwargs
    if args:
        key_parts.append(str(args))
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))
    
    # Create hash of key parts
    key_str = ':'.join(key_parts)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"cache:{prefix}:{key_hash}" if prefix else f"cache:{key_hash}"

def invalidate_cache(key_prefix):
    """
    Invalidate all cache entries with given prefix
    
    Usage:
        invalidate_cache('user_stats')
    """
    cache = get_cache()
    
    # For Redis, we can use pattern matching
    if isinstance(cache, RedisCache):
        try:
            pattern = f"cache:{key_prefix}:*"
            keys = cache.client.keys(pattern)
            if keys:
                cache.client.delete(*keys)
                print(f"Invalidated {len(keys)} cache entries with prefix: {key_prefix}")
        except Exception as e:
            print(f"Cache invalidation error: {e}")
    else:
        # For in-memory cache, clear all
        cache.clear()
        print(f"Cleared entire cache (in-memory mode)")

def cache_stats():
    """Get cache statistics"""
    cache = get_cache()
    
    if isinstance(cache, RedisCache):
        try:
            info = cache.client.info('stats')
            return {
                'type': 'redis',
                'keys': cache.client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'memory_used': cache.client.info('memory').get('used_memory_human', 'N/A')
            }
        except Exception as e:
            return {'error': str(e)}
    else:
        return {
            'type': 'in-memory',
            'keys': len(cache._cache)
        }

# Example usage
if __name__ == "__main__":
    print("Testing Redis Cache...")
    
    try:
        cache = get_cache()
        
        # Test set/get
        cache.set('test_key', {'message': 'Hello Redis'}, timeout=60)
        value = cache.get('test_key')
        print(f"Set and get test: {value}")
        
        # Test decorator
        @cached(timeout=10, key_prefix='test')
        def expensive_function(x):
            print(f"  Executing expensive_function({x})")
            return x * 2
        
        print("\nFirst call (cache miss):")
        result1 = expensive_function(5)
        print(f"Result: {result1}")
        
        print("\nSecond call (cache hit):")
        result2 = expensive_function(5)
        print(f"Result: {result2}")
        
        # Stats
        print(f"\nCache stats: {cache_stats()}")
        
        print("\n✓ Redis cache test completed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nNote: Make sure Redis is installed and running:")
        print("  Windows: Download from https://github.com/microsoftarchive/redis/releases")
        print("  Linux: sudo apt-get install redis-server")
        print("  Mac: brew install redis")
