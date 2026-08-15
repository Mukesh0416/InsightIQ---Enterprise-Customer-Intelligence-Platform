"""
Middleware package for the InsightIQ FastAPI application.

Provides modular middleware components that can be composed in ``main.py``:
    - CORS
    - Request logging
    - Response timing
    - Request ID injection
    - Trusted host validation

Usage:
    from app.middleware import configure_middleware

    app = FastAPI()
    configure_middleware(app)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.middleware.cors import configure_cors
from app.middleware.logging import configure_request_logging
from app.middleware.request_id import configure_request_id
from app.middleware.timing import configure_response_timing


def configure_middleware(app: FastAPI) -> None:
    """
    Register all middleware on the FastAPI application.

    Order matters: middleware is executed in reverse registration order
    (last added runs first for incoming requests).

    Args:
        app: The FastAPI application instance.
    """
    configure_cors(app)
    configure_request_id(app)
    configure_response_timing(app)
    configure_request_logging(app)

    # Trusted Host (last to be added, first to run on incoming)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )


__all__ = [
    "configure_middleware",
    "configure_cors",
    "configure_request_logging",
    "configure_response_timing",
    "configure_request_id",
]