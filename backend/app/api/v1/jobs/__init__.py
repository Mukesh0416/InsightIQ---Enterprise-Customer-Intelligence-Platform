"""
Background Jobs API endpoints.

GET    /jobs
GET    /jobs/{id}
DELETE /jobs/{id}
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import JobResponse
from app.services.jobs import JobEngine

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


@router.get("", summary="List background jobs")
async def list_jobs(
    organization_id: UUID = Query(...),
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("jobs.view")),
) -> dict:
    engine = JobEngine(session)
    jobs, total = await engine.list_jobs(organization_id, status=status, job_type=job_type, skip=skip, limit=limit)
    return {
        "items": [JobResponse.model_validate(j) for j in jobs],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{job_id}", response_model=JobResponse, summary="Get job by ID")
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("jobs.view")),
) -> JobResponse:
    from app.exceptions import NotFoundError
    engine = JobEngine(session)
    job = await engine.get_job(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=204, response_class=Response, summary="Cancel a job")
async def cancel_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("jobs.manage")),
) -> Response:
    engine = JobEngine(session)
    cancelled = await engine.cancel(job_id, current_user.id)
    if not cancelled:
        from app.exceptions import ValidationError
        raise ValidationError("Job cannot be cancelled (not pending/retrying or not found).")
    return Response(status_code=204)
