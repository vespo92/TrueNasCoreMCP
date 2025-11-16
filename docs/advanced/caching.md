# Caching Layer

The TrueNAS MCP Server includes a sophisticated caching layer to improve performance and reduce load on the TrueNAS API.

## Overview

The caching system provides:

- **In-memory cache** with TTL (Time To Live)
- **LRU eviction** when cache size limit is reached
- **Namespace support** for organizing cache entries
- **Cache statistics** for monitoring hit rates
- **Automatic cleanup** of expired entries

## Configuration

Configure caching via environment variables:

```env
ENABLE_CACHE=true
CACHE_TTL=300              # Default TTL in seconds (5 minutes)
CACHE_MAX_SIZE=1000        # Maximum cache entries
```

## Using the Cache

### Decorator-based Caching

The easiest way to use caching is with decorators:

```python
from truenas_mcp_server.cache import cached

@cached(ttl=300, namespace="pools")
async def get_pool_info(pool_name: str):
    # Expensive API call
    return await client.get(f"/api/v2.0/pool/{pool_name}")

# First call: Cache miss, hits API
pool = await get_pool_info("tank")

# Second call within TTL: Cache hit, returns cached data
pool = await get_pool_info("tank")
```

### Manual Cache Usage

For more control, use the cache manager directly:

```python
from truenas_mcp_server.cache import get_cache_manager

cache = get_cache_manager()

# Set value
await cache.set("pool:tank", pool_data, ttl=300)

# Get value
pool_data = await cache.get("pool:tank")

# Check if exists
if await cache.exists("pool:tank"):
    print("Cache hit!")

# Delete specific key
await cache.delete("pool:tank")

# Clear namespace
await cache.clear(namespace="pools")

# Clear all cache
await cache.clear()
```

## Cache Namespaces

Organize related cache entries using namespaces:

```python
# Storage-related cache
@cached(namespace="storage")
async def get_datasets():
    pass

# User-related cache
@cached(namespace="users")
async def get_users():
    pass

# Clear only storage cache
cache = get_cache_manager()
await cache.clear(namespace="storage")
```

## Cache Invalidation

### Manual Invalidation

Use the `@cache_invalidate` decorator to clear cache after modifications:

```python
from truenas_mcp_server.cache import cache_invalidate

@cache_invalidate(namespace="pools")
async def create_pool(pool_data):
    result = await client.post("/api/v2.0/pool", json=pool_data)
    # Cache for pools namespace is now cleared
    return result
```

### Conditional Caching

Cache only successful responses:

```python
from truenas_mcp_server.cache import conditional_cache

@conditional_cache(
    lambda result: result.get("success") is True,
    ttl=300,
    namespace="api"
)
async def api_call():
    return await make_request()
```

## Cache Statistics

Monitor cache performance:

```python
cache = get_cache_manager()
stats = cache.get_stats()

print(f"Hit rate: {stats['hit_rate']}%")
print(f"Cache size: {stats['size']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

Example output:
```json
{
  "hits": 1250,
  "misses": 320,
  "sets": 320,
  "deletes": 50,
  "evictions": 15,
  "size": 305,
  "hit_rate": 79.62
}
```

## Best Practices

### 1. Choose Appropriate TTL

- **Static data** (pool topology): Long TTL (3600s)
- **Semi-dynamic data** (dataset info): Medium TTL (300s)
- **Dynamic data** (system status): Short TTL (60s)

```python
@cached(ttl=3600)  # 1 hour
async def get_pool_topology():
    pass

@cached(ttl=300)  # 5 minutes
async def get_dataset_info():
    pass

@cached(ttl=60)  # 1 minute
async def get_system_status():
    pass
```

### 2. Use Namespaces

Group related cache entries for easy invalidation:

```python
# All pool-related data in "pools" namespace
@cached(namespace="pools")
async def list_pools():
    pass

@cached(namespace="pools")
async def get_pool_details(name):
    pass

# Invalidate all pool cache after changes
@cache_invalidate(namespace="pools")
async def create_pool(data):
    pass
```

### 3. Monitor Hit Rates

Track cache effectiveness:

```python
import logging

cache = get_cache_manager()
stats = cache.get_stats()

if stats['hit_rate'] < 50:
    logging.warning(f"Low cache hit rate: {stats['hit_rate']}%")
```

### 4. Size Cache Appropriately

Configure cache size based on your needs:

- **Small deployments**: 500-1000 entries
- **Medium deployments**: 1000-5000 entries
- **Large deployments**: 5000-10000 entries

## Advanced Features

### Custom Cache Keys

Generate custom cache keys:

```python
@cached(key_func=lambda pool, dataset: f"dataset:{pool}/{dataset}")
async def get_dataset(pool: str, dataset: str):
    pass
```

### Conditional Caching

Only cache when conditions are met:

```python
@conditional_cache(
    lambda result: len(result) > 0,  # Only cache non-empty results
    ttl=300
)
async def search_items(query: str):
    pass
```

### Background Cleanup

The cache automatically cleans up expired entries every minute. You can also trigger manual cleanup:

```python
cache = get_cache_manager()
await cache._cleanup_expired()
```

## Performance Impact

Typical performance improvements:

- **First call**: API latency (~100-500ms)
- **Cached call**: Memory access (~1-5ms)
- **Speed improvement**: 20-100x faster

## Memory Usage

Estimate memory usage:

```
Per entry: ~1KB (varies by data size)
1000 entries: ~1MB
10000 entries: ~10MB
```

## Troubleshooting

### High Memory Usage

Reduce cache size or TTL:

```env
CACHE_MAX_SIZE=500
CACHE_TTL=180
```

### Low Hit Rate

Increase TTL for stable data:

```python
@cached(ttl=1800)  # 30 minutes for stable data
```

### Stale Data

Reduce TTL or implement better invalidation:

```python
@cached(ttl=60)  # Shorter TTL
# Or
@cache_invalidate(namespace="data")
async def update_data():
    pass
```
