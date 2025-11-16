"""Unit tests for exception handling."""

import pytest

from truenas_mcp_server.exceptions import (
    TrueNASError,
    TrueNASConnectionError,
    TrueNASAuthenticationError,
    TrueNASAPIError,
    TrueNASTimeoutError,
    TrueNASRateLimitError,
    TrueNASValidationError,
    TrueNASNotFoundError,
    TrueNASPermissionError,
    TrueNASConfigurationError,
)


class TestTrueNASError:
    """Test base TrueNAS exception."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        error = TrueNASError("Test error")
        assert str(error) == "Test error"
        assert error.details is None

    def test_exception_with_details(self):
        """Test exception with details dict."""
        details = {"code": 500, "endpoint": "/api/v2/pool"}
        error = TrueNASError("API error", details=details)
        assert str(error) == "API error"
        assert error.details == details
        assert error.details["code"] == 500

    def test_exception_inheritance(self):
        """Test exception is instance of base Exception."""
        error = TrueNASError("Test")
        assert isinstance(error, Exception)


class TestConnectionError:
    """Test connection error handling."""

    def test_connection_error_creation(self):
        """Test connection error with details."""
        error = TrueNASConnectionError(
            "Failed to connect",
            details={"host": "truenas.local", "port": 443}
        )
        assert "Failed to connect" in str(error)
        assert error.details["host"] == "truenas.local"

    def test_inheritance(self):
        """Test connection error inherits from base."""
        error = TrueNASConnectionError("Test")
        assert isinstance(error, TrueNASError)


class TestAuthenticationError:
    """Test authentication error handling."""

    def test_auth_error_creation(self):
        """Test authentication error."""
        error = TrueNASAuthenticationError(
            "Invalid API key",
            details={"status_code": 401}
        )
        assert "Invalid API key" in str(error)
        assert error.details["status_code"] == 401

    def test_inheritance(self):
        """Test auth error inherits from base."""
        error = TrueNASAuthenticationError("Test")
        assert isinstance(error, TrueNASError)


class TestAPIError:
    """Test API error handling."""

    def test_api_error_with_status_code(self):
        """Test API error with HTTP status code."""
        error = TrueNASAPIError(
            "Bad request",
            details={
                "status_code": 400,
                "response": {"error": "Invalid dataset name"}
            }
        )
        assert error.details["status_code"] == 400
        assert "Invalid dataset name" in str(error.details["response"]["error"])

    def test_api_error_minimal(self):
        """Test API error with minimal info."""
        error = TrueNASAPIError("Unknown error")
        assert str(error) == "Unknown error"


class TestTimeoutError:
    """Test timeout error handling."""

    def test_timeout_error(self):
        """Test timeout error creation."""
        error = TrueNASTimeoutError(
            "Request timeout",
            details={"timeout": 30.0, "endpoint": "/api/v2/pool"}
        )
        assert "timeout" in str(error).lower()
        assert error.details["timeout"] == 30.0

    def test_inheritance(self):
        """Test timeout error inherits from base."""
        error = TrueNASTimeoutError("Test")
        assert isinstance(error, TrueNASError)


class TestRateLimitError:
    """Test rate limit error handling."""

    def test_rate_limit_error(self):
        """Test rate limit error with retry info."""
        error = TrueNASRateLimitError(
            "Rate limit exceeded",
            details={
                "limit": 100,
                "remaining": 0,
                "reset_time": 1704067200
            }
        )
        assert "rate limit" in str(error).lower()
        assert error.details["limit"] == 100
        assert error.details["remaining"] == 0

    def test_inheritance(self):
        """Test rate limit error inherits from base."""
        error = TrueNASRateLimitError("Test")
        assert isinstance(error, TrueNASError)


class TestValidationError:
    """Test validation error handling."""

    def test_validation_error_with_fields(self):
        """Test validation error with field info."""
        error = TrueNASValidationError(
            "Invalid input",
            details={
                "fields": ["username", "email"],
                "errors": ["Username too short", "Invalid email format"]
            }
        )
        assert "Invalid input" in str(error)
        assert "username" in error.details["fields"]

    def test_inheritance(self):
        """Test validation error inherits from base."""
        error = TrueNASValidationError("Test")
        assert isinstance(error, TrueNASError)


class TestNotFoundError:
    """Test not found error handling."""

    def test_not_found_error(self):
        """Test not found error with resource info."""
        error = TrueNASNotFoundError(
            "Dataset not found",
            details={"resource": "dataset", "id": "tank/nonexistent"}
        )
        assert "not found" in str(error).lower()
        assert error.details["id"] == "tank/nonexistent"

    def test_inheritance(self):
        """Test not found error inherits from base."""
        error = TrueNASNotFoundError("Test")
        assert isinstance(error, TrueNASError)


class TestPermissionError:
    """Test permission error handling."""

    def test_permission_error(self):
        """Test permission error with operation info."""
        error = TrueNASPermissionError(
            "Operation not permitted",
            details={
                "operation": "delete_user",
                "resource": "root",
                "reason": "Cannot delete system user"
            }
        )
        assert "not permitted" in str(error).lower()
        assert error.details["operation"] == "delete_user"

    def test_inheritance(self):
        """Test permission error inherits from base."""
        error = TrueNASPermissionError("Test")
        assert isinstance(error, TrueNASError)


class TestConfigurationError:
    """Test configuration error handling."""

    def test_configuration_error(self):
        """Test configuration error with config details."""
        error = TrueNASConfigurationError(
            "Invalid configuration",
            details={
                "setting": "truenas_url",
                "value": "invalid-url",
                "reason": "Must be a valid URL"
            }
        )
        assert "configuration" in str(error).lower()
        assert error.details["setting"] == "truenas_url"

    def test_inheritance(self):
        """Test configuration error inherits from base."""
        error = TrueNASConfigurationError("Test")
        assert isinstance(error, TrueNASError)


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_exception_from_another(self):
        """Test exception chaining with from."""
        original = ValueError("Original error")
        try:
            raise TrueNASAPIError("API error occurred") from original
        except TrueNASAPIError as e:
            assert e.__cause__ is original
            assert isinstance(e.__cause__, ValueError)

    def test_exception_context_preserved(self):
        """Test exception context is preserved."""
        try:
            try:
                raise ValueError("Original")
            except ValueError:
                raise TrueNASConnectionError("Connection failed")
        except TrueNASConnectionError as e:
            assert e.__context__ is not None
            assert isinstance(e.__context__, ValueError)
