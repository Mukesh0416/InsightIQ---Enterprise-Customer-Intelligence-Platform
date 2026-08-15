"""
Logging package for the InsightIQ backend.

Provides centralised logging configuration with structured formatting,
console and file output, and log rotation.

Usage:
    from app.logging import configure_logging, get_logger

    configure_logging()           # Call once at startup
    logger = get_logger(__name__) # Use throughout the application
"""

from app.logging.config import configure_logging, StructuredFormatter

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger instance for the given name.

    Args:
        name: Usually ``__name__`` from the calling module.

    Returns:
        A configured ``Logger`` instance.
    """
    return logging.getLogger(name)


__all__ = [
    "configure_logging",
    "get_logger",
    "StructuredFormatter",
]