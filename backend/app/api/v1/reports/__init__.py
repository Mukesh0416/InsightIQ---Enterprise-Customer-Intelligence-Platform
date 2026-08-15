"""
Reports API endpoints.

POST /reports/generate
GET  /reports
GET  /reports/{id}
GET  /reports/download/{id}
DELETE /reports/{id}
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.services import ReportGenerateRequest, ReportResponse
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=202,
    summary="Generate a report",
    description="Queues a report generation job. Supported formats: pdf, excel, csv, json.",
)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports.generate")),
) -> ReportResponse:
    svc = ReportService(session)
    report = await svc.create_report(request, current_user.id)
    background_tasks.add_task(svc.run_report_job, report.id)
    return ReportResponse.model_validate(report)


@router.get(
    "",
    summary="List reports",
    description="Returns paginated reports for the current user or organization.",
)
async def list_reports(
    organization_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports.view")),
) -> dict:
    svc = ReportService(session)
    reports, total = await svc.list_reports(current_user.id, organization_id, skip=skip, limit=limit)
    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report by ID",
)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("reports.view")),
) -> ReportResponse:
    svc = ReportService(session)
    report = await svc.get_report(report_id)
    return ReportResponse.model_validate(report)


@router.get(
    "/download/{report_id}",
    summary="Download report file",
    description="Returns the generated report file. Report must have status=completed.",
)
async def download_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports.view")),
) -> FileResponse:
    svc = ReportService(session)
    return await svc.download_report(report_id, current_user.id)


@router.delete(
    "/{report_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a report",
)
async def delete_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports.delete")),
) -> Response:
    svc = ReportService(session)
    await svc.delete_report(report_id, current_user.id)
    return Response(status_code=204)
