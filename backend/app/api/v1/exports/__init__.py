"""
Exports API endpoints.

POST /exports
GET  /exports/{id}
GET  /exports/{id}/download
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import ExportRequest, ExportResponse
from app.services.exports import ExportService

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportResponse, status_code=202, summary="Create export job")
async def create_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("exports.create")),
) -> ExportResponse:
    """Queue an asynchronous data export. Supports csv, excel, pdf, json."""
    svc = ExportService(session)
    job = await svc.create_export(request, current_user.id)
    background_tasks.add_task(svc.run_export_job, job.id)
    return ExportResponse.model_validate(job)


@router.get("/{job_id}", response_model=ExportResponse, summary="Get export job status")
async def get_export(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("exports.view")),
) -> ExportResponse:
    svc = ExportService(session)
    job = await svc.get_export(job_id)
    return ExportResponse.model_validate(job)


@router.get("/{job_id}/download", summary="Download export file")
async def download_export(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("exports.view")),
) -> FileResponse:
    svc = ExportService(session)
    return await svc.download_export(job_id)
