"""
Dashboard API endpoints.

GET /dashboard/overview
GET /dashboard/kpis
GET /dashboard/widgets
GET /dashboard/activity
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import WidgetRequest
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    summary="Executive dashboard overview",
    description="Returns KPIs, customer/revenue/sales overviews, data quality, AI summary, and recent activity.",
)
async def get_overview(
    organization_id: UUID = Query(...),
    dataset_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    svc = DashboardService(session)
    return await svc.get_overview(organization_id, dataset_id)


@router.get(
    "/kpis",
    summary="KPI cards",
    description="Returns all executive KPI cards for a dataset.",
)
async def get_kpis(
    dataset_id: UUID = Query(...),
    organization_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    svc = DashboardService(session)
    return await svc.get_kpis(dataset_id, organization_id)


@router.post(
    "/widgets",
    summary="Widget data",
    description="Generate chart-ready JSON for any supported widget type.",
)
async def get_widget(
    request: WidgetRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    svc = DashboardService(session)
    return await svc.get_widget(request.widget_type, request.dataset_id, request.config)


@router.get(
    "/activity",
    summary="Activity feed",
    description="Returns paginated recent activity for an organization.",
)
async def get_activity(
    organization_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    svc = DashboardService(session)
    return await svc.get_activity(organization_id, skip=skip, limit=limit)
