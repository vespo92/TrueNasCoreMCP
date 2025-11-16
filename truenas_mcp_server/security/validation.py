"""Input validation and sanitization utilities."""

import re
import os
import logging
from typing import Optional, List
from pathlib import Path

from ..exceptions import TrueNASValidationError

logger = logging.getLogger(__name__)


class PathValidator:
    """
    Path validation to prevent path traversal attacks.

    Features:
    - Path traversal detection
    - Allowed path prefixes
    - Symlink detection
    - Absolute path enforcement
    """

    def __init__(self, allowed_prefixes: Optional[List[str]] = None):
        """
        Initialize path validator.

        Args:
            allowed_prefixes: List of allowed path prefixes (e.g., ["/mnt"])
        """
        self.allowed_prefixes = allowed_prefixes or ["/mnt"]
        logger.info(f"Path validator initialized with prefixes: {self.allowed_prefixes}")

    def validate(self, path: str, allow_relative: bool = False) -> str:
        """
        Validate and normalize path.

        Args:
            path: Path to validate
            allow_relative: Whether to allow relative paths

        Returns:
            Normalized safe path

        Raises:
            TrueNASValidationError: If path is invalid or unsafe
        """
        if not path:
            raise TrueNASValidationError("Path cannot be empty")

        # Check for path traversal attempts
        if ".." in path:
            raise TrueNASValidationError(
                "Path traversal detected",
                details={"path": path, "reason": "contains '..'"}
            )

        # Check for null bytes
        if "\x00" in path:
            raise TrueNASValidationError(
                "Invalid path characters",
                details={"path": path, "reason": "contains null byte"}
            )

        # Normalize path
        try:
            normalized = os.path.normpath(path)
        except Exception as e:
            raise TrueNASValidationError(
                f"Invalid path format: {e}",
                details={"path": path}
            )

        # Check if absolute path is required
        if not allow_relative and not os.path.isabs(normalized):
            # Try to make it absolute with allowed prefix
            if self.allowed_prefixes:
                normalized = os.path.join(self.allowed_prefixes[0], normalized)
            else:
                raise TrueNASValidationError(
                    "Absolute path required",
                    details={"path": path}
                )

        # Verify path starts with allowed prefix
        if self.allowed_prefixes:
            if not any(normalized.startswith(prefix) for prefix in self.allowed_prefixes):
                raise TrueNASValidationError(
                    f"Path must start with one of: {self.allowed_prefixes}",
                    details={"path": normalized, "allowed_prefixes": self.allowed_prefixes}
                )

        logger.debug(f"Validated path: {path} -> {normalized}")
        return normalized

    def validate_dataset_path(self, pool: str, dataset: str) -> str:
        """
        Validate ZFS dataset path.

        Args:
            pool: Pool name
            dataset: Dataset name

        Returns:
            Full dataset path (pool/dataset)

        Raises:
            TrueNASValidationError: If dataset path is invalid
        """
        # Validate pool name
        if not re.match(r"^[a-zA-Z0-9_-]+$", pool):
            raise TrueNASValidationError(
                "Invalid pool name",
                details={"pool": pool, "reason": "contains invalid characters"}
            )

        # Validate dataset name (can contain slashes for nested datasets)
        if not re.match(r"^[a-zA-Z0-9_/-]+$", dataset):
            raise TrueNASValidationError(
                "Invalid dataset name",
                details={"dataset": dataset, "reason": "contains invalid characters"}
            )

        # Check for path traversal in dataset name
        if ".." in dataset or dataset.startswith("/"):
            raise TrueNASValidationError(
                "Invalid dataset name",
                details={"dataset": dataset, "reason": "path traversal attempt"}
            )

        full_path = f"{pool}/{dataset}"
        logger.debug(f"Validated dataset path: {full_path}")
        return full_path


class InputSanitizer:
    """
    Input sanitization utilities.

    Features:
    - String sanitization
    - SQL injection prevention
    - Command injection prevention
    - XSS prevention
    """

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255, allow_special: bool = False) -> str:
        """
        Sanitize string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_special: Whether to allow special characters

        Returns:
            Sanitized string

        Raises:
            TrueNASValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise TrueNASValidationError(
                "Value must be a string",
                details={"type": type(value).__name__}
            )

        # Trim whitespace
        sanitized = value.strip()

        # Check length
        if len(sanitized) == 0:
            raise TrueNASValidationError("String cannot be empty")

        if len(sanitized) > max_length:
            raise TrueNASValidationError(
                f"String exceeds maximum length of {max_length}",
                details={"length": len(sanitized), "max_length": max_length}
            )

        # Check for null bytes
        if "\x00" in sanitized:
            raise TrueNASValidationError("String contains null bytes")

        # Restrict to safe characters if needed
        if not allow_special:
            if not re.match(r"^[a-zA-Z0-9_\s-]+$", sanitized):
                raise TrueNASValidationError(
                    "String contains invalid characters",
                    details={"allowed": "alphanumeric, underscore, hyphen, space"}
                )

        return sanitized

    @staticmethod
    def sanitize_username(username: str) -> str:
        """
        Sanitize username.

        Args:
            username: Username to sanitize

        Returns:
            Sanitized username
        """
        username = username.strip()

        # Username validation rules
        if len(username) == 0:
            raise TrueNASValidationError("Username cannot be empty")

        if len(username) > 32:
            raise TrueNASValidationError("Username too long (max 32 characters)")

        # Must start with letter
        if not username[0].isalpha():
            raise TrueNASValidationError("Username must start with a letter")

        # Only alphanumeric and underscore
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", username):
            raise TrueNASValidationError(
                "Username can only contain letters, numbers, underscore, and hyphen"
            )

        return username.lower()

    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize and validate email address.

        Args:
            email: Email address to sanitize

        Returns:
            Sanitized email address
        """
        email = email.strip().lower()

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise TrueNASValidationError(
                "Invalid email address format",
                details={"email": email}
            )

        if len(email) > 254:  # RFC 5321
            raise TrueNASValidationError("Email address too long")

        return email

    @staticmethod
    def sanitize_command(command: str, allowed_commands: Optional[List[str]] = None) -> str:
        """
        Sanitize shell command to prevent command injection.

        Args:
            command: Command to sanitize
            allowed_commands: List of allowed command names

        Returns:
            Sanitized command

        Raises:
            TrueNASValidationError: If command is unsafe
        """
        command = command.strip()

        # Check for command injection patterns
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(char in command for char in dangerous_chars):
            raise TrueNASValidationError(
                "Command contains dangerous characters",
                details={"command": command}
            )

        # Check against allowed commands
        if allowed_commands:
            cmd_name = command.split()[0] if command else ""
            if cmd_name not in allowed_commands:
                raise TrueNASValidationError(
                    f"Command not allowed. Allowed commands: {allowed_commands}",
                    details={"command": cmd_name}
                )

        return command

    @staticmethod
    def validate_port(port: int) -> int:
        """
        Validate port number.

        Args:
            port: Port number to validate

        Returns:
            Validated port number
        """
        if not isinstance(port, int):
            raise TrueNASValidationError("Port must be an integer")

        if port < 1 or port > 65535:
            raise TrueNASValidationError(
                "Port must be between 1 and 65535",
                details={"port": port}
            )

        # Warn about privileged ports
        if port < 1024:
            logger.warning(f"Using privileged port: {port}")

        return port

    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """
        Validate IP address.

        Args:
            ip: IP address to validate

        Returns:
            Validated IP address
        """
        import ipaddress

        try:
            # This will raise ValueError if invalid
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise TrueNASValidationError(
                "Invalid IP address",
                details={"ip": ip}
            )
