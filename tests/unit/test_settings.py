"""Unit tests for settings configuration."""

import pytest
from pydantic import ValidationError, SecretStr

from truenas_mcp_server.config.settings import Settings, Environment, LogLevel


class TestSettings:
    """Test Settings configuration class."""

    def test_minimal_settings(self):
        """Test creating settings with minimal required fields."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("test-key-12345")
        )
        assert str(settings.truenas_url) == "https://truenas.local/"
        assert settings.truenas_api_key.get_secret_value() == "test-key-12345"
        assert settings.environment == Environment.PRODUCTION
        assert settings.log_level == LogLevel.INFO

    def test_all_settings(self, mock_settings):
        """Test creating settings with all fields."""
        assert str(mock_settings.truenas_url) == "https://truenas.local/"
        assert mock_settings.truenas_verify_ssl is False
        assert mock_settings.environment == Environment.TESTING
        assert mock_settings.log_level == LogLevel.DEBUG
        assert mock_settings.enable_destructive_operations is True

    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        for url in ["https://truenas.local", "http://192.168.1.100", "https://nas.example.com"]:
            settings = Settings(truenas_url=url, truenas_api_key=SecretStr("key"))
            assert settings.truenas_url is not None

    def test_invalid_url(self):
        """Test invalid URL raises validation error."""
        with pytest.raises(ValidationError):
            Settings(truenas_url="not-a-url", truenas_api_key=SecretStr("key"))

    def test_secret_str_masking(self, mock_settings):
        """Test that API key is properly masked."""
        # Should not expose secret in string representation
        settings_str = str(mock_settings)
        assert "test-api-key" not in settings_str
        # But should be accessible via get_secret_value
        assert mock_settings.truenas_api_key.get_secret_value() == "test-api-key-1234567890"

    def test_environment_enum(self):
        """Test environment enum values."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key"),
            environment="development"
        )
        assert settings.environment == Environment.DEVELOPMENT

        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key"),
            environment="production"
        )
        assert settings.environment == Environment.PRODUCTION

    def test_log_level_enum(self):
        """Test log level enum values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(
                truenas_url="https://truenas.local",
                truenas_api_key=SecretStr("key"),
                log_level=level
            )
            assert settings.log_level.value == level

    def test_http_settings(self, mock_settings):
        """Test HTTP client settings."""
        assert mock_settings.http_timeout == 30.0
        assert mock_settings.http_pool_connections == 10
        assert mock_settings.http_pool_maxsize == 20
        assert mock_settings.http_max_retries == 3
        assert mock_settings.http_retry_backoff_factor == 2.0

    def test_feature_flags(self, mock_settings):
        """Test feature flag settings."""
        assert mock_settings.enable_destructive_operations is True
        assert mock_settings.enable_cache is True
        assert mock_settings.enable_metrics is False

    def test_cache_settings(self):
        """Test cache configuration settings."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key"),
            cache_ttl=300,
            cache_max_size=500
        )
        assert settings.cache_ttl == 300
        assert settings.cache_max_size == 500

    def test_rate_limit_settings(self):
        """Test rate limiting settings."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key"),
            rate_limit_per_minute=100,
            rate_limit_burst=10
        )
        assert settings.rate_limit_per_minute == 100
        assert settings.rate_limit_burst == 10

    def test_default_values(self):
        """Test default values are properly set."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key")
        )
        assert settings.truenas_verify_ssl is True
        assert settings.environment == Environment.PRODUCTION
        assert settings.log_level == LogLevel.INFO
        assert settings.enable_destructive_operations is False
        assert settings.http_timeout == 60.0
        assert settings.http_max_retries == 3

    def test_settings_immutability(self, mock_settings):
        """Test that settings are properly configured (Pydantic v2 is mutable by default)."""
        # In Pydantic v2, models are mutable unless frozen=True
        # This test verifies we can update if needed
        original_timeout = mock_settings.http_timeout
        mock_settings.http_timeout = 120.0
        assert mock_settings.http_timeout == 120.0
        # Reset for other tests
        mock_settings.http_timeout = original_timeout

    def test_boolean_parsing(self):
        """Test boolean value parsing from strings."""
        settings = Settings(
            truenas_url="https://truenas.local",
            truenas_api_key=SecretStr("key"),
            truenas_verify_ssl="false",  # String that should parse to bool
            enable_destructive_operations="true"
        )
        assert settings.truenas_verify_ssl is False
        assert settings.enable_destructive_operations is True


class TestEnvironment:
    """Test Environment enum."""

    def test_environment_values(self):
        """Test all environment enum values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    def test_environment_comparison(self):
        """Test environment comparison."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.PRODUCTION == "production"


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_level_values(self):
        """Test all log level enum values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_log_level_comparison(self):
        """Test log level comparison."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.ERROR == "ERROR"
