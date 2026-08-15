"""
Request logging middleware for the FastAPI application.

Logs every incoming request and its response status, duration, and size.
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next):
    """
    Log every HTTP request handled by the application.

    Captures method, path, status code, and duration for observability.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "%s %s → %d (%0.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        extra={
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
            }
        },
    )
    return response


def configure_request_logging(app: FastAPI) -> None:
    """
    Add request-logging middleware to the application.

    Args:
        app: The FastAPI application instance.
    """
    app.middleware("http")(request_logging_middleware)