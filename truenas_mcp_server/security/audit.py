"""Audit logging for security-sensitive operations."""

import json
import logging
import time
from typing import Any, Dict, Optional
from functools import lru_cache
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AuditLevel(str, Enum):
    """Audit event severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AuditCategory(str, Enum):
    """Audit event categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


@dataclass
class AuditEvent:
    """Audit event record."""

    timestamp: float = field(default_factory=time.time)
    level: AuditLevel = AuditLevel.INFO
    category: AuditCategory = AuditCategory.SYSTEM
    action: str = ""
    resource: str = ""
    user: Optional[str] = None
    source_ip: Optional[str] = None
    result: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        data = asdict(self)
        data["timestamp_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self.timestamp))
        return data

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for security-sensitive operations.

    Features:
    - Structured audit logging
    - Multiple severity levels
    - Event categorization
    - JSON export
    - Retention policies
    """

    def __init__(self, max_events: int = 10000):
        """
        Initialize audit logger.

        Args:
            max_events: Maximum number of events to keep in memory
        """
        self.max_events = max_events
        self._events: list[AuditEvent] = []
        self._logger = logging.getLogger("truenas_mcp.audit")

        # Configure audit log handler
        self._setup_logging()

        logger.info("Audit logger initialized")

    def _setup_logging(self):
        """Set up audit log file handler."""
        # Create audit-specific handler
        handler = logging.FileHandler("truenas_mcp_audit.log")
        handler.setLevel(logging.INFO)

        # Use JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)

        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def log(
        self,
        action: str,
        resource: str,
        level: AuditLevel = AuditLevel.INFO,
        category: AuditCategory = AuditCategory.SYSTEM,
        user: Optional[str] = None,
        source_ip: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """
        Log an audit event.

        Args:
            action: Action performed (e.g., "create_user", "delete_dataset")
            resource: Resource affected (e.g., "user:john", "dataset:tank/data")
            level: Event severity level
            category: Event category
            user: User who performed the action
            source_ip: Source IP address
            result: Operation result ("success" or "failure")
            details: Additional event details
            error: Error message if operation failed
        """
        event = AuditEvent(
            level=level,
            category=category,
            action=action,
            resource=resource,
            user=user,
            source_ip=source_ip,
            result=result,
            details=details or {},
            error=error,
        )

        # Add to in-memory store
        self._events.append(event)

        # Trim if exceeds max
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]

        # Write to audit log
        log_level = getattr(logging, level.value)
        self._logger.log(log_level, event.to_json())

        # Also log to main logger for critical events
        if level == AuditLevel.CRITICAL:
            logger.critical(
                f"AUDIT: {action} on {resource} by {user or 'unknown'}: {result}"
            )

    def log_authentication(
        self, user: str, success: bool, source_ip: Optional[str] = None, details: Optional[Dict] = None
    ):
        """Log authentication attempt."""
        self.log(
            action="authenticate",
            resource=f"user:{user}",
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            category=AuditCategory.AUTHENTICATION,
            user=user,
            source_ip=source_ip,
            result="success" if success else "failure",
            details=details,
        )

    def log_data_modification(
        self,
        action: str,
        resource: str,
        user: Optional[str] = None,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None,
    ):
        """Log data modification."""
        details = {}
        if before:
            details["before"] = before
        if after:
            details["after"] = after

        self.log(
            action=action,
            resource=resource,
            level=AuditLevel.WARNING,
            category=AuditCategory.DATA_MODIFICATION,
            user=user,
            details=details,
        )

    def log_destructive_operation(
        self, action: str, resource: str, user: Optional[str] = None, details: Optional[Dict] = None
    ):
        """Log destructive operation (delete, destroy, etc.)."""
        self.log(
            action=action,
            resource=resource,
            level=AuditLevel.CRITICAL,
            category=AuditCategory.DATA_MODIFICATION,
            user=user,
            result="success",
            details=details,
        )

    def log_permission_denied(
        self, action: str, resource: str, user: Optional[str] = None, reason: Optional[str] = None
    ):
        """Log permission denied event."""
        self.log(
            action=action,
            resource=resource,
            level=AuditLevel.WARNING,
            category=AuditCategory.AUTHORIZATION,
            user=user,
            result="failure",
            error=reason or "Permission denied",
        )

    def get_events(
        self,
        limit: int = 100,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        user: Optional[str] = None,
    ) -> list[AuditEvent]:
        """
        Get audit events with optional filtering.

        Args:
            limit: Maximum number of events to return
            level: Filter by severity level
            category: Filter by category
            user: Filter by user

        Returns:
            List of audit events
        """
        events = self._events

        # Apply filters
        if level:
            events = [e for e in events if e.level == level]
        if category:
            events = [e for e in events if e.category == category]
        if user:
            events = [e for e in events if e.user == user]

        # Return most recent first
        return list(reversed(events[-limit:]))

    def export_json(self, limit: int = 1000) -> str:
        """
        Export audit events as JSON.

        Args:
            limit: Maximum number of events to export

        Returns:
            JSON string of events
        """
        events = self.get_events(limit=limit)
        return json.dumps([e.to_dict() for e in events], indent=2)

    def clear_events(self):
        """Clear all in-memory events."""
        count = len(self._events)
        self._events.clear()
        logger.info(f"Cleared {count} audit events from memory")


# Global audit logger
_audit_logger: Optional[AuditLogger] = None


@lru_cache(maxsize=1)
def get_audit_logger() -> AuditLogger:
    """
    Get or create global audit logger.

    Returns:
        Global AuditLogger instance
    """
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger()
        logger.info("Created global audit logger")

    return _audit_logger
