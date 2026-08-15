"""
Global exception handlers for the FastAPI application.

Registers handlers that catch ``InsightIQError`` subclasses, Pydantic
validation errors, and unhandled exceptions, returning a consistent
JSON error response structure.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.exceptions import InsightIQError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI app.

    Call this during application startup (usually in ``main.py``).

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(InsightIQError)
    async def insightiq_error_handler(
        request: Request,
        exc: InsightIQError,
    ) -> JSONResponse:
        """Handle all custom ``InsightIQError`` exceptions."""
        logger.warning(
            "Application error: %s (status=%d)",
            exc.message,
            exc.status_code,
            extra={
                "extra_fields": {
                    "path": str(request.url.path),
                    "method": request.method,
                    "status_code": exc.status_code,
                }
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.message,
                    "detail": exc.detail,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(PydanticValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError | PydanticValidationError,
    ) -> JSONResponse:
        """Handle Pydantic / FastAPI request validation errors."""
        errors = getattr(exc, "errors", lambda: [{"msg": str(exc)}])()
        logger.warning(
            "Validation error: %s", str(errors),
            extra={
                "extra_fields": {
                    "path": str(request.url.path),
                    "method": request.method,
                }
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": 422,
                    "message": "Request validation failed",
                    "detail": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all handler for any unhandled exception."""
        logger.exception(
            "Unhandled exception: %s", str(exc),
            extra={
                "extra_fields": {
                    "path": str(request.url.path),
                    "method": request.method,
                }
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "detail": None,
                }
            },
        )