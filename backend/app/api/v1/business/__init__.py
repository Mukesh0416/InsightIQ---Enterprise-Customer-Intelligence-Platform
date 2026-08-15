"""Business analytics API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.services.business import BusinessAnalyticsService

router = APIRouter(prefix="/business", tags=["Business Analytics"])


@router.get("/customer-overview/{dataset_id}")
async def customer_overview(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get total, new, returning, active, inactive customers and growth metrics."""
    service = BusinessAnalyticsService(session)
    return await service.customer_overview(dataset_id)


@router.get("/customer-growth/{dataset_id}")
async def customer_growth(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get customer growth rate, new vs returning split."""
    service = BusinessAnalyticsService(session)
    return await service.customer_growth(dataset_id)


@router.get("/revenue/{dataset_id}")
async def revenue(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get total, monthly, quarterly revenue, and growth."""
    service = BusinessAnalyticsService(session)
    return await service.revenue_analysis(dataset_id)


@router.get("/sales/{dataset_id}")
async def sales(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get total, monthly, daily sales, AOV, top products/customers."""
    service = BusinessAnalyticsService(session)
    return await service.sales_analysis(dataset_id)


@router.get("/retention/{dataset_id}")
async def retention(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get retention rate, repeat purchase rate, churn, customer age."""
    service = BusinessAnalyticsService(session)
    return await service.retention_analysis(dataset_id)


@router.get("/rfm/{dataset_id}")
async def rfm(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get RFM segmentation: champions, loyal, at-risk, lost customers."""
    service = BusinessAnalyticsService(session)
    return await service.rfm_analysis(dataset_id)


@router.get("/cohort/{dataset_id}")
async def cohort(
    dataset_id: UUID,
    period: str = Query("monthly", pattern="^(monthly|weekly)$"),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get cohort retention, revenue, and repeat purchase matrices."""
    service = BusinessAnalyticsService(session)
    return await service.cohort_analysis(dataset_id, period)


@router.get("/clv/{dataset_id}")
async def clv(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get Customer Lifetime Value: historical, predictive, top CLV."""
    service = BusinessAnalyticsService(session)
    return await service.clv_analysis(dataset_id)


@router.get("/kpis/{dataset_id}")
async def kpis(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get executive KPI cards: revenue, ARPU, churn, retention, AOV."""
    service = BusinessAnalyticsService(session)
    return await service.kpis(dataset_id)


@router.get("/trends/{dataset_id}")
async def trends(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get MoM, QoQ, YoY trends, moving averages, growth/decline periods."""
    service = BusinessAnalyticsService(session)
    return await service.trends(dataset_id)


@router.get("/recommendations/{dataset_id}")
async def recommendations(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get intelligent business recommendations: retain, win-back, upsell, cross-sell."""
    service = BusinessAnalyticsService(session)
    return await service.recommendations(dataset_id)


@router.get("/report/{dataset_id}")
async def report(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get the complete executive business report with all analytics modules."""
    service = BusinessAnalyticsService(session)
    return await service.report(dataset_id)