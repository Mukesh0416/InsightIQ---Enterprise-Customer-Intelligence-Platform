"""
Business analytics service that orchestrates all business analytics modules.

Loads dataset files and runs customer, sales, revenue, retention, RFM,
cohort, CLV, KPI, trend, recommendation, and report generation.
"""

from __future__ import annotations

import importlib
import io
import logging
import time
from typing import Any, cast
from uuid import UUID

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.business.customer import CustomerAnalytics
from app.analytics.business.kpi import KPIEngine, TrendAnalyzer
from app.analytics.business.recommendations import ExecutiveSummaryEngine, RecommendationEngine
from app.analytics.business.retention import CohortAnalyzer, RetentionAnalytics, RFMAnalyzer
from app.analytics.business.revenue import RevenueAnalytics
from app.exceptions import NotFoundError
from app.repositories.dataset import DatasetRepository
from app.storage import get_storage_provider

_sales_module = importlib.import_module("app.analytics.business.sales")


class _FallbackSalesAnalytics:
    @staticmethod
    def analyze(df: pd.DataFrame) -> dict[str, Any]:
        raise NotImplementedError("Sales analytics implementation is unavailable.")


SalesAnalytics = cast(
    type[_FallbackSalesAnalytics],
    getattr(_sales_module, "SalesAnalytics", None)
    or getattr(_sales_module, "SalesAnalyticsEngine", None)
    or getattr(_sales_module, "SalesAnalyzer", None)
    or _FallbackSalesAnalytics,
)

logger = logging.getLogger(__name__)


class BusinessAnalyticsService:
    """Orchestrates the complete business analytics pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DatasetRepository(session)
        self.storage = get_storage_provider()

    async def _load_dataframe(self, dataset_id: UUID) -> pd.DataFrame:
        """Load the current version's file into a pandas DataFrame."""
        from app.models.dataset import Dataset

        dataset = await self.session.get(Dataset, dataset_id)
        if not dataset or dataset.is_deleted:
            raise NotFoundError(f"Dataset {dataset_id} not found.")
        version = await self.repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        file = await self.repo.get_file_by_version(version.id)
        if not file:
            raise NotFoundError("No stored file for current version.")
        data = await self.storage.read(file.storage_path)
        ext = file.file_extension
        if ext == ".csv":
            return pd.read_csv(io.BytesIO(data))
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(io.BytesIO(data))
        raise NotFoundError(f"Unsupported file extension: {ext}")

    async def customer_overview(self, dataset_id: UUID) -> dict[str, Any]:
        logger.info("Business analysis started: customer overview %s", dataset_id)
        df = await self._load_dataframe(dataset_id)
        return CustomerAnalytics.analyze(df)

    async def customer_growth(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        result = CustomerAnalytics.analyze(df)
        return {
            "total_customers": result["total_customers"],
            "new_customers": result["new_customers"],
            "returning_customers": result["returning_customers"],
            "customer_growth_rate": result["customer_growth_rate"],
            "active_customers": result["active_customers"],
            "inactive_customers": result["inactive_customers"],
        }

    async def revenue_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return RevenueAnalytics.analyze(df)

    async def sales_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return SalesAnalytics.analyze(df)

    async def retention_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return RetentionAnalytics.analyze(df)

    async def rfm_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return RFMAnalyzer.analyze(df)

    async def cohort_analysis(self, dataset_id: UUID, period: str = "monthly") -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return CohortAnalyzer.analyze(df, period)

    async def clv_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return RetentionAnalytics.compute_clv(df)

    async def kpis(self, dataset_id: UUID) -> dict[str, Any]:
        logger.info("KPI generation started for dataset: %s", dataset_id)
        df = await self._load_dataframe(dataset_id)
        result = KPIEngine.compute(df)
        logger.info("KPI generation completed for dataset: %s", dataset_id)
        return result

    async def trends(self, dataset_id: UUID) -> dict[str, Any]:
        df = await self._load_dataframe(dataset_id)
        return TrendAnalyzer.analyze(df)

    async def recommendations(self, dataset_id: UUID) -> dict[str, Any]:
        logger.info("Recommendation generation started for dataset: %s", dataset_id)
        df = await self._load_dataframe(dataset_id)
        result = RecommendationEngine.generate(df)
        logger.info("Recommendation generation completed for dataset: %s", dataset_id)
        return result

    async def report(self, dataset_id: UUID) -> dict[str, Any]:
        logger.info("Report generation started for dataset: %s", dataset_id)
        start = time.perf_counter()
        df = await self._load_dataframe(dataset_id)

        report = {
            "dataset_id": str(dataset_id),
            "executive_summary": ExecutiveSummaryEngine.generate(df),
            "customer": CustomerAnalytics.analyze(df),
            "revenue": RevenueAnalytics.analyze(df),
            "sales": SalesAnalytics.analyze(df),
            "retention": RetentionAnalytics.analyze(df),
            "kpis": KPIEngine.compute(df),
            "trends": TrendAnalyzer.analyze(df),
            "recommendations": RecommendationEngine.generate(df),
            "processing_time_ms": round((time.perf_counter() - start) * 1000, 2),
        }
        logger.info("Report generation completed for dataset: %s", dataset_id)
        return report