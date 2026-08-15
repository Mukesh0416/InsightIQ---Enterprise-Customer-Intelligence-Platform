"""
Pydantic schemas for health-check endpoints.

Defines the request/response models used by the ``/health``, ``/ready``,
and ``/live`` endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for the health-check response."""

    status: str = Field(
        ...,
        description="Overall service status (e.g. 'healthy', 'degraded').",
    )
    version: str = Field(
        ...,
        description="Application version string.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check.",
    )
    database: str = Field(
        ...,
        description="Database connectivity status ('connected' | 'disconnected').",
    )


class ReadinessResponse(BaseModel):
    """Schema for the readiness probe response."""

    status: str = Field(
        ...,
        description="Readiness status ('ready' | 'not_ready').",
    )
    dependencies: dict[str, str] = Field(
        ...,
        description="Status of each external dependency.",
    )


class LivenessResponse(BaseModel):
    """Schema for the liveness probe response."""

    status: str = Field(
        ...,
        description="Liveness status ('alive').",
    )