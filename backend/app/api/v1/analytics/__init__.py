"""
Interactive Analytics API endpoints.

GET /analytics/customer
GET /analytics/revenue
GET /analytics/sales
GET /analytics/retention
GET /analytics/cohort
GET /analytics/rfm
GET /analytics/trends
GET /analytics/recommendations
GET /analytics/clv
GET /analytics/eda
GET /analytics/correlation
GET /analytics/forecast
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.services.business import BusinessAnalyticsService
from app.services.eda import EDAService

router = APIRouter(prefix="/analytics", tags=["Interactive Analytics"])


def _biz(session: AsyncSession) -> BusinessAnalyticsService:
    return BusinessAnalyticsService(session)


def _eda(session: AsyncSession) -> EDAService:
    return EDAService(session)


@router.get("/customer", summary="Customer analytics")
async def customer_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Total, new, returning, active, inactive customers and growth metrics."""
    return await _biz(session).customer_overview(dataset_id)


@router.get("/revenue", summary="Revenue analytics")
async def revenue_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Total, monthly, quarterly revenue, growth, and breakdown by customer/region/product."""
    return await _biz(session).revenue_analysis(dataset_id)


@router.get("/sales", summary="Sales analytics")
async def sales_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Total sales, AOV, top products, top customers, daily/monthly/yearly breakdown."""
    return await _biz(session).sales_analysis(dataset_id)


@router.get("/retention", summary="Retention analytics")
async def retention_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Retention rate, repeat purchase rate, churn, customer survival."""
    return await _biz(session).retention_analysis(dataset_id)


@router.get("/cohort", summary="Cohort analysis")
async def cohort_analytics(
    dataset_id: UUID = Query(...),
    period: str = Query("monthly", pattern="^(monthly|weekly)$"),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Cohort retention, revenue, and repeat purchase matrices."""
    return await _biz(session).cohort_analysis(dataset_id, period)


@router.get("/rfm", summary="RFM segmentation")
async def rfm_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """RFM segments: champions, loyal, at-risk, lost customers."""
    return await _biz(session).rfm_analysis(dataset_id)


@router.get("/clv", summary="Customer Lifetime Value")
async def clv_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Historical and predictive CLV per customer."""
    return await _biz(session).clv_analysis(dataset_id)


@router.get("/trends", summary="Trend analysis")
async def trend_analytics(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """MoM, QoQ, YoY trends, moving averages, growth/decline periods."""
    return await _biz(session).trends(dataset_id)


@router.get("/recommendations", summary="Business recommendations")
async def recommendations(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Intelligent business recommendations: retain, win-back, upsell, cross-sell."""
    return await _biz(session).recommendations(dataset_id)


@router.get("/eda", summary="EDA summary")
async def eda_summary(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Dataset-level EDA summary: shape, types, missing, duplicates."""
    return await _eda(session).get_summary(dataset_id)


@router.get("/correlation", summary="Correlation analysis")
async def correlation_summary(
    dataset_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Pearson/Spearman correlation matrix and top correlated pairs."""
    return await _eda(session).get_correlation(dataset_id)


@router.get("/forecast", summary="Revenue forecast")
async def forecast_summary(
    dataset_id: UUID = Query(...),
    periods: int = Query(6, ge=1, le=24),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
) -> dict:
    """Monthly revenue forecast for the next N periods."""
    from app.services.business_ai import RevenueForecastingService
    from app.services.business import BusinessAnalyticsService
    import io
    import pandas as pd
    from app.repositories.dataset import DatasetRepository
    from app.storage import get_storage_provider

    repo = DatasetRepository(session)
    storage = get_storage_provider()
    version = await repo.get_current_version(dataset_id)
    if not version:
        from app.exceptions import NotFoundError
        raise NotFoundError("Dataset has no current version.")
    file = await repo.get_file_by_version(version.id)
    if not file:
        from app.exceptions import NotFoundError
        raise NotFoundError("No stored file for current version.")
    data = await storage.read(file.storage_path)
    df = pd.read_csv(io.BytesIO(data)) if file.file_extension == ".csv" else pd.read_excel(io.BytesIO(data))
    return RevenueForecastingService.forecast(df, periods=periods)
