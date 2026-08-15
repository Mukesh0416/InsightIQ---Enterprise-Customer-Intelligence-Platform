"""
Health-check endpoints for infrastructure monitoring.

Provides three standard probes:
    - ``/health`` – overall system health including database status.
    - ``/ready``  – readiness probe (are all dependencies available?).
    - ``/live``   – liveness probe (is the process alive?).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.database.session import verify_database_connection
from app.schemas.health import HealthResponse, LivenessResponse, ReadinessResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the overall health status of the service, including database connectivity.",
)
async def health_check() -> HealthResponse:
    """
    Perform a comprehensive health check.

    Verifies that the database is reachable and returns the application
    version and current timestamp.
    """
    db_ok = await verify_database_connection()
    status = "healthy" if db_ok else "degraded"

    logger.info(
        "Health check: status=%s database=%s",
        status,
        "connected" if db_ok else "disconnected",
    )

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database="connected" if db_ok else "disconnected",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Indicates whether the service is ready to accept traffic.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Perform a readiness probe.

    Checks that all external dependencies are available. Returns a
    detailed map of dependency statuses.
    """
    db_ok = await verify_database_connection()
    dependencies = {
        "database": "connected" if db_ok else "disconnected",
    }
    status = "ready" if db_ok else "not_ready"

    return ReadinessResponse(
        status=status,
        dependencies=dependencies,
    )


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Indicates whether the service process is alive.",
)
async def liveness_check() -> LivenessResponse:
    """
    Perform a liveness probe.

    Returns a simple ``alive`` response. This endpoint does not check
    dependencies; it only confirms the process is running.
    """
    return LivenessResponse(status="alive")