"""
Configuration and environment management for the backend service.

Exposes the global ``settings`` singleton and application constants.
Import from this module rather than instantiating Settings directly:
    from app.config import settings
    from app.config.constants import AppEnv
"""

from app.config.settings import Settings, settings
from app.config.constants import (
    AppEnv,
    LogLevel,
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    API_CONTACT,
    API_LICENSE_INFO,
    TAGS_METADATA,
    REQUEST_ID_HEADER,
    CORRELATION_ID_HEADER,
    DATETIME_FORMAT,
    DATE_FORMAT,
)

__all__ = [
    "Settings",
    "settings",
    "AppEnv",
    "LogLevel",
    "API_TITLE",
    "API_VERSION",
    "API_DESCRIPTION",
    "API_CONTACT",
    "API_LICENSE_INFO",
    "TAGS_METADATA",
    "REQUEST_ID_HEADER",
    "CORRELATION_ID_HEADER",
    "DATETIME_FORMAT",
    "DATE_FORMAT",
]