"""
Redis Cache Service
Provides caching functionality for frequently accessed data
"""
import redis
import json
import os
from functools import wraps
from flask import request

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    REDIS_ENABLED = True
    print("✅ Redis connection successful")
except (redis.ConnectionError, redis.TimeoutError) as e:
    print(f"⚠️  Redis connection failed: {e}. Caching disabled.")
    redis_client = None
    REDIS_ENABLED = False

def cache_key(*args, **kwargs):
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)

def cached(timeout=300, key_prefix=""):
    """
    Decorator to cache function results in Redis
    
    Args:
        timeout: Cache expiration time in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    
    Example:
        @cached(timeout=600, key_prefix="user_profile")
        def get_user_profile(user_id):
            # Expensive database query
            return user_data
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not REDIS_ENABLED or not redis_client:
                # If Redis is disabled, just call the function
                return f(*args, **kwargs)
            
            # Generate cache key
            key = f"{key_prefix}:{cache_key(*args, **kwargs)}"
            
            try:
                # Try to get from cache
                cached_value = redis_client.get(key)
                if cached_value:
                    print(f"🎯 Cache hit: {key}")
                    return json.loads(cached_value)
                
                # Cache miss - call the function
                print(f"💾 Cache miss: {key}")
                result = f(*args, **kwargs)
                
                # Store in cache
                redis_client.setex(key, timeout, json.dumps(result))
                return result
                
            except Exception as e:
                print(f"⚠️  Cache error: {e}. Falling back to direct call.")
                return f(*args, **kwargs)
        
        return wrapped
    return decorator

def invalidate_cache(pattern):
    """
    Invalidate cache keys matching a pattern
    
    Args:
        pattern: Redis key pattern (e.g., "user_profile:user_123*")
    
    Example:
        invalidate_cache("user_profile:user_123*")
    """
    if not REDIS_ENABLED or not redis_client:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            print(f"🗑️  Invalidated {len(keys)} cache keys matching '{pattern}'")
    except Exception as e:
        print(f"⚠️  Cache invalidation error: {e}")

def clear_all_cache():
    """Clear all cache (use with caution!)"""
    if not REDIS_ENABLED or not redis_client:
        return
    
    try:
        redis_client.flushdb()
        print("🗑️  All cache cleared")
    except Exception as e:
        print(f"⚠️  Cache clear error: {e}")

def get_cache_stats():
    """Get cache statistics"""
    if not REDIS_ENABLED or not redis_client:
        return {"enabled": False, "message": "Redis not available"}
    
    try:
        info = redis_client.info('stats')
        return {
            "enabled": True,
            "total_keys": redis_client.dbsize(),
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "hit_rate": round(info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2)
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}

# Cache common queries
@cached(timeout=600, key_prefix="health_tips")
def get_health_tips_cached():
    """Cache health tips for 10 minutes"""
    # This would be called from the route
    pass

@cached(timeout=1800, key_prefix="ml_model_predictions")
def cache_ml_prediction(user_id, age, screen_time, sleep_hours, diet_quality):
    """Cache ML predictions for 30 minutes"""
    # This would be called from the prediction route
    pass
