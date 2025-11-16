"""Metrics collector for monitoring and observability."""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from functools import lru_cache
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class Counter:
    """Simple counter metric."""

    name: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def inc(self, amount: int = 1):
        """Increment counter."""
        self.value += amount

    def reset(self):
        """Reset counter to zero."""
        self.value = 0


@dataclass
class Gauge:
    """Gauge metric that can go up and down."""

    name: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float):
        """Set gauge value."""
        self.value = value

    def inc(self, amount: float = 1.0):
        """Increment gauge."""
        self.value += amount

    def dec(self, amount: float = 1.0):
        """Decrement gauge."""
        self.value -= amount


@dataclass
class Histogram:
    """Histogram for tracking distributions."""

    name: str
    buckets: List[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    observations: List[float] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    sum: float = 0.0
    count: int = 0

    def observe(self, value: float):
        """Observe a value."""
        self.observations.append(value)
        self.sum += value
        self.count += 1

    def get_quantile(self, q: float) -> float:
        """Get quantile value (0.0 to 1.0)."""
        if not self.observations:
            return 0.0
        sorted_obs = sorted(self.observations)
        index = int(q * len(sorted_obs))
        return sorted_obs[min(index, len(sorted_obs) - 1)]

    def get_stats(self) -> Dict[str, float]:
        """Get histogram statistics."""
        if not self.observations:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        return {
            "count": self.count,
            "sum": self.sum,
            "mean": statistics.mean(self.observations),
            "min": min(self.observations),
            "max": max(self.observations),
            "p50": self.get_quantile(0.50),
            "p95": self.get_quantile(0.95),
            "p99": self.get_quantile(0.99),
        }


class MetricsCollector:
    """
    Metrics collector for monitoring application performance.

    Features:
    - Counters (monotonically increasing)
    - Gauges (up/down values)
    - Histograms (distributions)
    - Prometheus export format
    - Labels support
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._start_time = time.time()

        logger.info("Metrics collector initialized")

    def counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
        """
        Get or create a counter.

        Args:
            name: Counter name
            labels: Optional labels for metric

        Returns:
            Counter instance
        """
        key = self._make_key(name, labels)

        if key not in self._counters:
            self._counters[key] = Counter(name=name, labels=labels or {})

        return self._counters[key]

    def gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """
        Get or create a gauge.

        Args:
            name: Gauge name
            labels: Optional labels for metric

        Returns:
            Gauge instance
        """
        key = self._make_key(name, labels)

        if key not in self._gauges:
            self._gauges[key] = Gauge(name=name, labels=labels or {})

        return self._gauges[key]

    def histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Histogram:
        """
        Get or create a histogram.

        Args:
            name: Histogram name
            labels: Optional labels for metric

        Returns:
            Histogram instance
        """
        key = self._make_key(name, labels)

        if key not in self._histograms:
            self._histograms[key] = Histogram(name=name, labels=labels or {})

        return self._histograms[key]

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create unique key for metric with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """
        Record HTTP request metrics.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration in seconds
        """
        labels = {"endpoint": endpoint, "method": method, "status": str(status_code)}

        # Increment request counter
        self.counter("http_requests_total", labels).inc()

        # Record duration
        self.histogram("http_request_duration_seconds", labels).observe(duration)

        # Track errors
        if status_code >= 400:
            self.counter("http_errors_total", labels).inc()

    def record_cache_hit(self, namespace: Optional[str] = None):
        """Record cache hit."""
        labels = {"namespace": namespace} if namespace else {}
        self.counter("cache_hits_total", labels).inc()

    def record_cache_miss(self, namespace: Optional[str] = None):
        """Record cache miss."""
        labels = {"namespace": namespace} if namespace else {}
        self.counter("cache_misses_total", labels).inc()

    def record_rate_limit(self, key: str, allowed: bool):
        """Record rate limit check."""
        labels = {"key": key, "allowed": str(allowed)}
        self.counter("rate_limit_checks_total", labels).inc()

    def set_cache_size(self, size: int):
        """Set cache size gauge."""
        self.gauge("cache_size").set(float(size))

    def set_active_connections(self, count: int):
        """Set active connections gauge."""
        self.gauge("active_connections").set(float(count))

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics as dictionary.

        Returns:
            Dictionary of all metrics
        """
        return {
            "counters": {
                key: {"name": c.name, "value": c.value, "labels": c.labels}
                for key, c in self._counters.items()
            },
            "gauges": {
                key: {"name": g.name, "value": g.value, "labels": g.labels}
                for key, g in self._gauges.items()
            },
            "histograms": {
                key: {"name": h.name, "stats": h.get_stats(), "labels": h.labels}
                for key, h in self._histograms.items()
            },
            "uptime_seconds": time.time() - self._start_time,
        }

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics
        """
        lines = []

        # Add counters
        for key, counter in self._counters.items():
            lines.append(f"# TYPE {counter.name} counter")
            label_str = self._format_labels(counter.labels)
            lines.append(f"{counter.name}{label_str} {counter.value}")

        # Add gauges
        for key, gauge in self._gauges.items():
            lines.append(f"# TYPE {gauge.name} gauge")
            label_str = self._format_labels(gauge.labels)
            lines.append(f"{gauge.name}{label_str} {gauge.value}")

        # Add histograms
        for key, hist in self._histograms.items():
            lines.append(f"# TYPE {hist.name} histogram")
            label_str = self._format_labels(hist.labels)
            stats = hist.get_stats()

            # Add histogram buckets
            for bucket in hist.buckets:
                count = sum(1 for obs in hist.observations if obs <= bucket)
                lines.append(f'{hist.name}_bucket{{le="{bucket}"{label_str[1:]} {count}')

            lines.append(f"{hist.name}_sum{label_str} {stats['sum']}")
            lines.append(f"{hist.name}_count{label_str} {stats['count']}")

        # Add uptime
        uptime = time.time() - self._start_time
        lines.append("# TYPE process_uptime_seconds gauge")
        lines.append(f"process_uptime_seconds {uptime}")

        return "\n".join(lines) + "\n"

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus export."""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"

    def reset_all(self):
        """Reset all metrics."""
        for counter in self._counters.values():
            counter.reset()

        for gauge in self._gauges.values():
            gauge.set(0.0)

        for histogram in self._histograms.values():
            histogram.observations.clear()
            histogram.sum = 0.0
            histogram.count = 0

        logger.info("All metrics reset")


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


@lru_cache(maxsize=1)
def get_metrics_collector() -> MetricsCollector:
    """
    Get or create global metrics collector.

    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        logger.info("Created global metrics collector")

    return _metrics_collector
