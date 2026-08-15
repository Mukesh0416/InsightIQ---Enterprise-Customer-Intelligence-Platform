"""
Custom exception classes and global exception handlers for the InsightIQ API.

Provides a hierarchy of typed exceptions and FastAPI exception handlers
that return consistent, structured error responses.
"""

from __future__ import annotations

from typing import Any


class InsightIQError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        detail: Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(InsightIQError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        detail: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=404, detail=detail)


class ConflictError(InsightIQError):
    """Raised when a request conflicts with the current state."""

    def __init__(
        self,
        message: str = "Resource already exists",
        detail: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=409, detail=detail)


class ValidationError(InsightIQError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        detail: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=422, detail=detail)


class ServiceUnavailableError(InsightIQError):
    """Raised when an external dependency is unreachable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        detail: Any = None,
    ) -> None:
        super().__init__(message=message, status_code=503, detail=detail)


__all__ = [
    "InsightIQError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "ServiceUnavailableError",
]