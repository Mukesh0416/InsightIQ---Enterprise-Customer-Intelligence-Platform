"""EDA API endpoints for data profiling and exploratory data analysis."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.services.eda import EDAService

router = APIRouter(prefix="/eda", tags=["EDA"])


@router.get("/{dataset_id}/summary")
async def get_summary(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get dataset-level summary: rows, columns, memory, missing, duplicates."""
    service = EDAService(session)
    return await service.get_summary(dataset_id)


@router.get("/{dataset_id}/profile")
async def get_profile(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get per-column profiles with type, stats, entropy, and quality metrics."""
    service = EDAService(session)
    return await service.get_profile(dataset_id)


@router.get("/{dataset_id}/statistics")
async def get_statistics(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get detailed numerical and categorical statistics for all columns."""
    service = EDAService(session)
    return await service.get_statistics(dataset_id)


@router.get("/{dataset_id}/missing")
async def get_missing(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get missing value analysis: overall, per-column, per-row, heatmap data."""
    service = EDAService(session)
    return await service.get_missing_analysis(dataset_id)


@router.get("/{dataset_id}/duplicates")
async def get_duplicates(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get duplicate row and column analysis."""
    service = EDAService(session)
    return await service.get_duplicates(dataset_id)


@router.get("/{dataset_id}/outliers")
async def get_outliers(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get outlier detection results (IQR, Z-score, Modified Z-score)."""
    service = EDAService(session)
    return await service.get_outliers(dataset_id)


@router.get("/{dataset_id}/correlation")
async def get_correlation(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get correlation analysis: Pearson, Spearman, Kendall, VIF, highly correlated pairs."""
    service = EDAService(session)
    return await service.get_correlation(dataset_id)


@router.get("/{dataset_id}/distribution")
async def get_distribution(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get distribution analysis: normal, skewed, uniform detection per column."""
    service = EDAService(session)
    return await service.get_distribution(dataset_id)


@router.get("/{dataset_id}/quality")
async def get_quality(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get data quality insights: missing, duplicates, constants, cardinality, mixed types."""
    service = EDAService(session)
    return await service.get_quality(dataset_id)


@router.get("/{dataset_id}/insights")
async def get_insights(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    """Get business insights and recommendations: encoding, scaling, feature engineering."""
    service = EDAService(session)
    return await service.get_insights(dataset_id)