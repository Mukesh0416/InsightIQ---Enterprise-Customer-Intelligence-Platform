"""
Common Pydantic schemas used across the API.

Provides reusable response wrappers, pagination models, and error
response structures.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response body returned by all API errors."""

    code: int = Field(..., description="HTTP status code of the error.")
    message: str = Field(..., description="Human-readable error message.")
    detail: Any = Field(None, description="Additional error details or validation errors.")


class ErrorWrapper(BaseModel):
    """Wrapper around ``ErrorResponse`` for consistent JSON structure."""

    error: ErrorResponse


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page.")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated responses."""

    items: list[T] = Field(..., description="List of items for the current page.")
    total: int = Field(..., description="Total number of items across all pages.")
    page: int = Field(..., description="Current page number.")
    page_size: int = Field(..., description="Number of items per page.")
    total_pages: int = Field(..., description="Total number of pages.")