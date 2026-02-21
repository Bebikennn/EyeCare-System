"""
Test Redis Cache Implementation
Run this to verify Redis cache is working
"""
import sys
import os

# Test 1: Import modules
print("Test 1: Importing modules...")
try:
    from utils.redis_cache import RedisCache, cached
    print("✓ Successfully imported redis_cache module")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Check Redis connection (with fallback)
print("\nTest 2: Testing Redis connection...")
cache = RedisCache()

if cache.redis_client:
    print("✓ Redis connected successfully")
    connection_type = "Redis"
else:
    print("⚠ Redis not available, using in-memory fallback")
    connection_type = "In-Memory"

# Test 3: Basic cache operations
print(f"\nTest 3: Testing basic cache operations ({connection_type})...")
try:
    # Set value
    cache.set('test_key', 'Hello World', timeout=60)
    print("✓ Set value: test_key = 'Hello World'")
    
    # Get value
    value = cache.get('test_key')
    assert value == 'Hello World', f"Expected 'Hello World', got {value}"
    print(f"✓ Get value: test_key = '{value}'")
    
    # Check exists
    exists = cache.exists('test_key')
    assert exists is True, "Key should exist"
    print("✓ Key exists check passed")
    
    # Delete value
    cache.delete('test_key')
    print("✓ Deleted test_key")
    
    # Verify deletion
    value = cache.get('test_key')
    assert value is None, f"Expected None, got {value}"
    print("✓ Verified deletion (value is None)")
    
except Exception as e:
    print(f"✗ Cache operation failed: {e}")
    sys.exit(1)

# Test 4: Decorator caching
print("\nTest 4: Testing @cached decorator...")
try:
    call_count = 0
    
    @cached(timeout=60, key_prefix='test_func')
    def expensive_function(x, y):
        global call_count
        call_count += 1
        return x + y
    
    # First call - should execute function
    result1 = expensive_function(5, 3)
    assert result1 == 8, f"Expected 8, got {result1}"
    assert call_count == 1, f"Expected call_count=1, got {call_count}"
    print(f"✓ First call: expensive_function(5, 3) = {result1}, call_count = {call_count}")
    
    # Second call - should use cache
    result2 = expensive_function(5, 3)
    assert result2 == 8, f"Expected 8, got {result2}"
    assert call_count == 1, f"Expected call_count=1 (cached), got {call_count}"
    print(f"✓ Second call: expensive_function(5, 3) = {result2}, call_count = {call_count} (cached)")
    
    # Different args - should execute function
    result3 = expensive_function(10, 20)
    assert result3 == 30, f"Expected 30, got {result3}"
    assert call_count == 2, f"Expected call_count=2, got {call_count}"
    print(f"✓ Third call: expensive_function(10, 20) = {result3}, call_count = {call_count}")
    
except Exception as e:
    print(f"✗ Decorator test failed: {e}")
    sys.exit(1)

# Test 5: Cache invalidation
print("\nTest 5: Testing cache invalidation...")
try:
    # Set multiple values with same prefix
    cache.set('user:1:name', 'Alice', timeout=60)
    cache.set('user:2:name', 'Bob', timeout=60)
    cache.set('user:3:name', 'Charlie', timeout=60)
    cache.set('product:1:name', 'Widget', timeout=60)
    print("✓ Set multiple cached values")
    
    # Invalidate by prefix
    deleted_count = cache.invalidate_by_prefix('user:')
    print(f"✓ Invalidated {deleted_count} keys with prefix 'user:'")
    
    # Verify user keys deleted
    assert cache.get('user:1:name') is None, "user:1:name should be deleted"
    assert cache.get('user:2:name') is None, "user:2:name should be deleted"
    print("✓ Verified user keys deleted")
    
    # Verify product key still exists
    assert cache.get('product:1:name') == 'Widget', "product:1:name should still exist"
    print("✓ Verified product key still exists")
    
    # Cleanup
    cache.delete('product:1:name')
    
except Exception as e:
    print(f"✗ Invalidation test failed: {e}")
    sys.exit(1)

# Test 6: Cache statistics
print("\nTest 6: Testing cache statistics...")
try:
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")
    
    if connection_type == "Redis":
        assert 'memory_used_bytes' in stats, "Redis stats should include memory_used_bytes"
        print(f"  - Memory used: {stats.get('memory_used_bytes', 0)} bytes")
        print(f"  - Keys: {stats.get('keys', 0)}")
    else:
        print("  - In-memory cache (no detailed stats)")
    
except Exception as e:
    print(f"✗ Stats test failed: {e}")
    sys.exit(1)

# Test 7: Clear all cache
print("\nTest 7: Testing cache clear...")
try:
    # Set some values
    cache.set('temp1', 'value1', timeout=60)
    cache.set('temp2', 'value2', timeout=60)
    
    # Clear all
    cache.clear()
    print("✓ Cleared all cache")
    
    # Verify cleared
    assert cache.get('temp1') is None, "temp1 should be cleared"
    assert cache.get('temp2') is None, "temp2 should be cleared"
    print("✓ Verified all keys cleared")
    
except Exception as e:
    print(f"✗ Clear test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 50)
print("✅ All cache tests passed!")
print("=" * 50)
print(f"\nCache Type: {connection_type}")

if connection_type == "In-Memory":
    print("\n⚠ WARNING: Redis server not running!")
    print("\nTo use Redis:")
    print("1. Install Redis server:")
    print("   - Windows: https://github.com/microsoftarchive/redis/releases")
    print("   - WSL: sudo apt install redis-server")
    print("2. Start Redis: redis-server")
    print("3. Test connection: redis-cli PING")
    print("4. Run this test again")
else:
    print("\n✓ Redis is properly configured and working!")
    print("\nYou can now:")
    print("1. Use @cached decorator in your routes")
    print("2. Manually cache data with cache.set()/cache.get()")
    print("3. Invalidate cache with cache.delete() or invalidate_by_prefix()")
    print("4. Monitor with cache.get_stats()")

print("\nExample usage in routes:")
print("""
from utils.redis_cache import cached

@app.route('/api/users')
@cached(timeout=300, key_prefix='users_list')
def get_users():
    # This will be cached for 5 minutes
    users = fetch_users_from_db()
    return jsonify(users)
""")
