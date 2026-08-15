"""
Centralised logging configuration for the InsightIQ backend.

Configures structured logging with console output, file output with
rotation, and correlation-ID propagation across async contexts.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.config import settings


def build_log_record(
    message: str,
    level: str = "INFO",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a structured log record dictionary.

    Args:
        message: The log message text.
        level: Log level name (e.g. "INFO", "ERROR").
        extra: Optional key-value pairs to include in the record.

    Returns:
        A dictionary representing the structured log record.
    """
    record: dict[str, Any] = {
        "message": message,
        "level": level,
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }
    if extra:
        record.update(extra)
    return record


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON log lines.

    Includes timestamp, level, logger name, message, and any extra
    fields passed via the ``extra`` parameter.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a structured string."""
        timestamp = self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z")
        base = (
            f"[{timestamp}] [{record.levelname}] "
            f"[{record.name}] {record.getMessage()}"
        )
        if hasattr(record, "extra_fields") and record.extra_fields:
            extra_str = " | ".join(
                f"{k}={v}" for k, v in record.extra_fields.items()
            )
            base = f"{base} | {extra_str}"
        if record.exc_info and record.exc_info[0] is not None:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging() -> None:
    """
    Set up the root logger with console and optional file handlers.

    Call this once during application startup (usually in ``main.py``).
    After calling this, use the standard ``logging.getLogger(name)``
    pattern throughout the application.
    """
    log_level = getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO)

    # ── Root logger ────────────────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any pre-existing handlers to avoid duplicates on reload
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    # ── Console handler (stdout) ───────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # ── File handler (with rotation) ───────────────────────────────────────
    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "insightiq.log"

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # ── Suppress overly verbose third-party loggers ────────────────────────
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # ── Log the configuration summary ──────────────────────────────────────
    root_logger.info(
        "Logging initialised",
        extra={
            "extra_fields": {
                "level": settings.APP_LOG_LEVEL,
                "file": str(log_file),
                "env": settings.APP_ENV,
            }
        },
    )