"""
Unit tests for the application configuration module.

Tests that settings are loaded correctly from environment variables
and that the constants module provides the expected values.
"""

from __future__ import annotations

from app.config import settings
from app.config.constants import (
    API_TITLE,
    API_VERSION,
    AppEnv,
    LogLevel,
)


def test_settings_default_app_name() -> None:
    """The default application name should be ``InsightIQ``."""
    assert settings.APP_NAME == "InsightIQ"


def test_settings_default_version() -> None:
    """The default version should be ``0.1.0``."""
    assert settings.APP_VERSION == "0.1.0"


def test_settings_default_env() -> None:
    """The default environment should be ``development``."""
    assert settings.APP_ENV == "development"


def test_settings_default_debug() -> None:
    """Debug mode should be enabled by default."""
    assert settings.APP_DEBUG is True


def test_settings_default_log_level() -> None:
    """The default log level should be ``INFO``."""
    assert settings.APP_LOG_LEVEL == "INFO"


def test_settings_database_url_default() -> None:
    """The default database URL should point to a local PostgreSQL instance."""
    assert "postgresql+psycopg://" in settings.DATABASE_URL
    assert "localhost" in settings.DATABASE_URL


def test_settings_api_prefix() -> None:
    """The API prefix should be ``/api/v1``."""
    assert settings.API_PREFIX == "/api/v1"


def test_settings_docs_urls() -> None:
    """Swagger docs and ReDoc URLs should be set correctly."""
    assert settings.API_DOCS_URL == "/docs"
    assert settings.API_REDOC_URL == "/redoc"
    assert settings.API_OPENAPI_URL == "/openapi.json"


def test_constants_api_title() -> None:
    """The API title constant should be ``InsightIQ API``."""
    assert API_TITLE == "InsightIQ API"


def test_constants_api_version() -> None:
    """The API version constant should be ``0.1.0``."""
    assert API_VERSION == "0.1.0"


def test_constants_app_env_enum() -> None:
    """The ``AppEnv`` enum should contain the expected values."""
    assert AppEnv.DEVELOPMENT == "development"
    assert AppEnv.STAGING == "staging"
    assert AppEnv.PRODUCTION == "production"


def test_constants_log_level_enum() -> None:
    """The ``LogLevel`` enum should contain the expected values."""
    assert LogLevel.INFO == "INFO"
    assert LogLevel.ERROR == "ERROR"
    assert LogLevel.DEBUG == "DEBUG"