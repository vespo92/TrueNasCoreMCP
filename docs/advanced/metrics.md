# Metrics & Monitoring

The TrueNAS MCP Server includes comprehensive metrics collection and monitoring capabilities.

## Overview

Features:

- **Prometheus-compatible** metrics export
- **Counters, Gauges, and Histograms**
- **Automatic request tracking**
- **Custom metrics support**
- **Performance monitoring**

## Configuration

Enable metrics:

```env
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Available Metrics

### Request Metrics

```
# HTTP request counter with labels
http_requests_total{endpoint="/api/v2.0/pool",method="GET",status="200"} 1523

# Request duration histogram
http_request_duration_seconds_bucket{endpoint="/api/v2.0/pool",le="0.5"} 1450
http_request_duration_seconds_sum{endpoint="/api/v2.0/pool"} 234.5
http_request_duration_seconds_count{endpoint="/api/v2.0/pool"} 1523

# Error counter
http_errors_total{endpoint="/api/v2.0/pool",method="GET",status="500"} 12
```

### Cache Metrics

```
# Cache hits
cache_hits_total{namespace="pools"} 1250

# Cache misses
cache_misses_total{namespace="pools"} 320

# Cache size gauge
cache_size 305
```

### Rate Limit Metrics

```
# Rate limit checks
rate_limit_checks_total{key="default",allowed="true"} 980
rate_limit_checks_total{key="default",allowed="false"} 20
```

### System Metrics

```
# Active connections
active_connections 15

# Process uptime
process_uptime_seconds 3456.78
```

## Using Metrics

### Automatic Tracking

Metrics are automatically collected for:

- HTTP requests
- Cache operations
- Rate limit checks

### Manual Metrics

Use the metrics collector directly:

```python
from truenas_mcp_server.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Increment counter
metrics.counter("custom_operations_total").inc()

# Set gauge
metrics.gauge("queue_size").set(42)

# Observe histogram value
metrics.histogram("operation_duration_seconds").observe(1.23)
```

### Decorators

Track function execution automatically:

```python
from truenas_mcp_server.metrics import track_time, track_counter, track_errors

@track_time()
async def slow_operation():
    # Automatically tracked in histogram
    pass

@track_counter("user_creations_total")
async def create_user():
    # Counter incremented on each call
    pass

@track_errors()
async def risky_operation():
    # Tracks successes and errors separately
    pass
```

## Prometheus Integration

### Scrape Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'truenas_mcp'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
```

### Example Queries

**Request rate:**
```promql
rate(http_requests_total[5m])
```

**Average request duration:**
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

**Cache hit rate:**
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100
```

**Error rate:**
```promql
rate(http_errors_total[5m])
```

**P95 latency:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Grafana Dashboard

Example dashboard panels:

### Request Rate
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

### Error Rate
```promql
sum(rate(http_errors_total[5m])) by (status)
```

### Response Time (P50, P95, P99)
```promql
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Cache Performance
```promql
rate(cache_hits_total[5m])
rate(cache_misses_total[5m])
```

## Custom Metrics

### Creating Custom Metrics

```python
from truenas_mcp_server.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Counter for tracking events
operations_counter = metrics.counter(
    "dataset_operations_total",
    labels={"operation": "create", "pool": "tank"}
)
operations_counter.inc()

# Gauge for current state
storage_gauge = metrics.gauge(
    "storage_used_bytes",
    labels={"pool": "tank"}
)
storage_gauge.set(1024 * 1024 * 1024 * 500)  # 500GB

# Histogram for distributions
size_histogram = metrics.histogram(
    "dataset_size_bytes",
    labels={"pool": "tank"}
)
size_histogram.observe(1024 * 1024 * 100)  # 100MB
```

### Labels

Add labels for better filtering:

```python
# Track operations per pool
for pool in ["tank", "backup"]:
    metrics.counter("pool_operations_total", labels={"pool": pool}).inc()

# Track by user
metrics.counter("user_actions_total", labels={"user": "admin", "action": "create"}).inc()
```

## Exporting Metrics

### Prometheus Format

```python
metrics = get_metrics_collector()
prometheus_text = metrics.export_prometheus()
print(prometheus_text)
```

Output:
```
# TYPE http_requests_total counter
http_requests_total{endpoint="/api/v2.0/pool",method="GET",status="200"} 1523
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/api/v2.0/pool",le="0.5"} 1450
http_request_duration_seconds_sum{endpoint="/api/v2.0/pool"} 234.5
http_request_duration_seconds_count{endpoint="/api/v2.0/pool"} 1523
```

### JSON Format

```python
metrics_dict = metrics.get_all_metrics()
print(json.dumps(metrics_dict, indent=2))
```

## Best Practices

### 1. Use Appropriate Metric Types

- **Counter**: Monotonically increasing (requests, errors)
- **Gauge**: Can go up/down (temperature, queue size)
- **Histogram**: Track distributions (latency, size)

### 2. Add Meaningful Labels

```python
# Good: Specific labels
metrics.counter("api_calls", labels={"endpoint": "/pool", "method": "GET"})

# Bad: Too generic
metrics.counter("calls")
```

### 3. Don't Over-Label

Avoid high-cardinality labels (user IDs, timestamps):

```python
# Bad: Creates millions of unique metrics
metrics.counter("requests", labels={"user_id": user_id})

# Good: Use grouping
metrics.counter("requests", labels={"user_type": "admin"})
```

### 4. Reset Periodically

Reset metrics when needed:

```python
metrics = get_metrics_collector()
metrics.reset_all()
```

## Alerting

Example Prometheus alerts:

```yaml
groups:
  - name: truenas_mcp
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "95th percentile latency > 2s"

      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 10m
        annotations:
          summary: "Cache hit rate below 50%"
```

## Troubleshooting

### Metrics Not Appearing

Check if metrics are enabled:

```python
from truenas_mcp_server.config import get_settings
settings = get_settings()
print(f"Metrics enabled: {settings.enable_metrics}")
```

### High Memory Usage

Reduce metric retention or use aggregation:

```python
# Reset metrics periodically
metrics.reset_all()
```

### Missing Labels

Ensure labels are consistent:

```python
# All calls must use same label keys
metrics.counter("requests", labels={"endpoint": "/pool", "method": "GET"})
metrics.counter("requests", labels={"endpoint": "/dataset", "method": "POST"})
```
