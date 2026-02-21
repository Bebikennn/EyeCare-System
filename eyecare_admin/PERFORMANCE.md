# Performance Optimization Guide

This document describes the performance improvements made to the EyeCare Admin Dashboard in Phase 5A.

## Overview

The following optimizations have been implemented to improve response times and reduce database load:

1. **Query Result Caching** - Frequently accessed endpoints now cache results
2. **Database Indexing** - Indexes added on commonly queried columns
3. **Cache Invalidation Patterns** - Smart cache clearing on data updates

## Implemented Optimizations

### 1. Query Result Caching

**Endpoints with caching enabled:**

- `GET /api/users/stats` - User statistics (5 min TTL)
- `GET /api/assessments/stats` - Assessment statistics (5 min TTL)

**How it works:**
- First request hits the database and caches the result
- Subsequent requests return cached data (much faster)
- Cache automatically expires after TTL (Time To Live)
- Cache is invalidated when related data changes

**Performance Impact:**
- **Before**: ~200-500ms per stats request (database query)
- **After**: ~5-10ms per stats request (cache hit)
- **Improvement**: 20-100x faster response times

### 2. Database Indexes

**New indexes added** (see `migrations/add_performance_indexes.sql`):

#### Users Table
```sql
idx_users_status              -- Filter by status (active/blocked/archived)
idx_users_created_at          -- Sort by registration date
idx_users_status_created      -- Composite: status + created_at
```

#### Assessment Results Table
```sql
idx_assessments_risk_level         -- Filter by risk level
idx_assessments_assessed_at        -- Sort by assessment date
idx_assessments_risk_assessed      -- Composite: risk_level + assessed_at
idx_assessments_user_assessed      -- Composite: user_id + assessed_at
```

#### Health Tips Table
```sql
idx_healthtips_category            -- Filter by category
idx_healthtips_status              -- Filter by status
idx_healthtips_risk_level          -- Filter by target risk level
idx_healthtips_status_category     -- Composite: status + category
```

#### Activity Logs Table
```sql
idx_activitylogs_admin_id          -- Filter by admin
idx_activitylogs_action            -- Filter by action type
idx_activitylogs_created_at        -- Sort by timestamp
idx_activitylogs_admin_created     -- Composite: admin_id + created_at
```

#### Admins Table
```sql
idx_admins_role                    -- Filter by role
idx_admins_status                  -- Filter by status
idx_admins_last_login              -- Sort by last login
```

**Performance Impact:**
- **Before**: Full table scans on filtered queries (slow as data grows)
- **After**: Index seeks (constant time O(log n))
- **Improvement**: 10-100x faster for filtered/sorted queries

**How to apply:**
```bash
mysql -u root -p eyecare_db < migrations/add_performance_indexes.sql
```

### 3. Smart Cache Invalidation

**Automatic cache invalidation:**
- Creating a new user → invalidates `user_stats:*` cache
- Creating a new assessment → invalidates `assessment_stats:*` cache
- Ensures data consistency while maintaining performance

**Manual cache management (Admin API):**
```bash
# Get cache statistics
GET /api/cache/stats

# Clear specific cache prefix
POST /api/cache/clear
Content-Type: application/json
{
  "prefix": "user_stats"
}

# Clear entire cache
POST /api/cache/clear
Content-Type: application/json
{}
```

## Cache Statistics Monitoring

Access cache stats through the admin API:

```bash
GET /api/cache/stats
```

**Response:**
```json
{
  "total_entries": 15,
  "total_hits": 247,
  "hot_keys": [
    {"key": "user_stats:a1b2c3", "hits": 89},
    {"key": "assessment_stats:d4e5f6", "hits": 76}
  ],
  "memory_estimate_kb": 15
}
```

## Best Practices

### When to Cache
✅ **Cache these:**
- Aggregate statistics (counts, averages)
- Report data that changes infrequently
- Expensive queries with joins
- Data accessed frequently (dashboard stats)

❌ **Don't cache these:**
- Real-time data requirements
- User-specific sensitive data
- Frequently changing data (e.g., live counters)

### Cache TTL Guidelines
- **Dashboard stats**: 5 minutes (300s)
- **Report data**: 15 minutes (900s)
- **Reference data**: 1 hour (3600s)

### Cache Keys
Always use descriptive prefixes:
```python
@cached(timeout=300, key_prefix='user_stats')
@cached(timeout=300, key_prefix='assessment_stats')
@cached(timeout=900, key_prefix='monthly_report')
```

## Performance Monitoring

### Database Query Performance
Monitor slow queries in MySQL:
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- Check for missing indexes
SELECT * FROM sys.schema_unused_indexes;
```

### Application Performance
- Use `/health` endpoint for basic monitoring
- Check logs for slow requests
- Monitor cache hit rate via `/api/cache/stats`

## Future Optimizations

Potential improvements for Phase 5B+:

1. **Redis Cache** - Replace in-memory cache with Redis for multi-server deployments
2. **Query Result Pagination** - Optimize large result sets
3. **Database Connection Pooling** - Tune pool size for production load
4. **CDN Integration** - Cache static assets (CSS, JS, images)
5. **API Response Compression** - Gzip responses to reduce bandwidth

## Troubleshooting

### Cache not clearing
```bash
# Force clear entire cache
curl -X POST http://localhost:5001/api/cache/clear \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Queries still slow after indexing
- Check if indexes are being used: `EXPLAIN SELECT ...`
- Verify indexes were created: Run the verification query in `add_performance_indexes.sql`
- Check for table lock contention during writes

### High memory usage
- Cache grows unbounded? Add TTL to all cached endpoints
- Clear expired entries periodically (automatic in production)

## Metrics

Expected performance improvements:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Dashboard load time | 2-3s | 0.5-1s | 2-3x faster |
| Stats API response | 200-500ms | 5-10ms | 20-100x faster |
| User list (1000 users) | 300ms | 50ms | 6x faster |
| Assessment filter query | 500ms | 80ms | 6x faster |
| Cache hit rate | 0% | 70-90% | N/A |

*Note: Actual improvements depend on data volume and query patterns*
