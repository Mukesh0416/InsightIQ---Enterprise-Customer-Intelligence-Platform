"""
Application-wide constants and metadata.

Centralises all magic strings, enumerations, and static values used
across the application to avoid duplication and improve maintainability.
"""

from __future__ import annotations

from enum import Enum


class AppEnv(str, Enum):
    """Valid application environment names."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Valid logging level names."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ── API Metadata ───────────────────────────────────────────────────────────
API_TITLE = "InsightIQ API"
API_VERSION = "0.1.0"
API_DESCRIPTION = """
Enterprise Customer Intelligence Platform.

Provides customer analytics, segmentation, churn prediction, forecasting,
and reporting capabilities through a RESTful API.
"""
API_CONTACT = {
    "name": "InsightIQ Support",
    "url": "https://insightiq.example.com/support",
    "email": "support@insightiq.example.com",
}
API_LICENSE_INFO = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

# ── Tags metadata ──────────────────────────────────────────────────────────
TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Health check and readiness probes for infrastructure monitoring.",
    },
]

# ── HTTP Header names ──────────────────────────────────────────────────────
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

# ── Date / Time formats ────────────────────────────────────────────────────
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
DATE_FORMAT = "%Y-%m-%d"