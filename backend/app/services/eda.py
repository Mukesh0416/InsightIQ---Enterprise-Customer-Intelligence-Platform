"""
EDA service that orchestrates all analytics modules.

Loads dataset files, runs profiling, statistics, outlier detection,
correlation, distribution analysis, quality insights, and visualization
data generation. Results are cached and can be reprocessed.
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.correlation.engine import CorrelationEngine
from app.analytics.distribution.analyzer import DistributionAnalyzer
from app.analytics.outliers.detector import OutlierDetector
from app.analytics.profiling.engine import ProfilingEngine
from app.analytics.quality.insights import QualityInsights
from app.analytics.statistics.categorical import CategoricalAnalyzer
from app.analytics.statistics.numerical import NumericalAnalyzer
from app.analytics.visualization.generator import VisualizationGenerator
from app.exceptions import NotFoundError
from app.repositories.dataset import DatasetRepository
from app.storage import get_storage_provider

logger = logging.getLogger(__name__)


class EDAService:
    """Orchestrates the complete EDA pipeline for a dataset."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DatasetRepository(session)
        self.storage = get_storage_provider()

    async def _load_dataframe(self, dataset_id: UUID) -> pd.DataFrame:
        """Load the current version's file into a pandas DataFrame."""
        dataset = await self.session.get(
            __import__("app.models.dataset", fromlist=["Dataset"]).Dataset, dataset_id
        )
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

    async def get_summary(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate dataset-level summary."""
        logger.info("EDA summary started for dataset: %s", dataset_id)
        df = await self._load_dataframe(dataset_id)
        result = ProfilingEngine.generate_summary(df)
        logger.info("EDA summary completed for dataset: %s", dataset_id)
        return result

    async def get_profile(self, dataset_id: UUID) -> list[dict[str, Any]]:
        """Generate per-column profiles."""
        logger.info("EDA profile started for dataset: %s", dataset_id)
        df = await self._load_dataframe(dataset_id)
        result = ProfilingEngine.profile_all_columns(df)
        logger.info("EDA profile completed for dataset: %s (%d columns)", dataset_id, len(result))
        return result

    async def get_statistics(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate detailed statistics for all columns."""
        df = await self._load_dataframe(dataset_id)
        from app.validators.type_detector import TypeDetector

        numeric_results: dict[str, Any] = {}
        categorical_results: dict[str, Any] = {}

        for col in df.columns:
            col_type = TypeDetector.detect_series_type(df[col])
            if col_type in ("integer", "float"):
                numeric_results[str(col)] = NumericalAnalyzer.analyze(df[col])
            elif col_type in ("categorical", "string", "boolean"):
                categorical_results[str(col)] = CategoricalAnalyzer.analyze(df[col])

        return {
            "numeric_columns": numeric_results,
            "categorical_columns": categorical_results,
        }

    async def get_missing_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate missing value analysis."""
        df = await self._load_dataframe(dataset_id)
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = int(df.isna().sum().sum())

        col_missing: dict[str, float] = {}
        for col in df.columns:
            col_missing[str(col)] = round(
                float(df[col].isna().mean() * 100), 2
            )

        row_missing_pct = df.isna().sum(axis=1) / df.shape[1]
        rows_with_missing = int((row_missing_pct > 0).sum())

        return {
            "overall_missing_pct": round(missing_cells / max(total_cells, 1) * 100, 2),
            "total_missing_cells": missing_cells,
            "column_missing_pct": col_missing,
            "rows_with_missing": rows_with_missing,
            "rows_with_missing_pct": round(rows_with_missing / max(df.shape[0], 1) * 100, 2),
            "missing_heatmap": VisualizationGenerator._generate_missing_heatmap(df),
        }

    async def get_duplicates(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate duplicate row/column analysis."""
        df = await self._load_dataframe(dataset_id)
        dup_rows = int(df.duplicated().sum())
        dup_cols = ProfilingEngine._find_duplicate_columns(df)
        return {
            "duplicate_rows": dup_rows,
            "duplicate_rows_pct": round(dup_rows / max(df.shape[0], 1) * 100, 2),
            "duplicate_columns": dup_cols,
            "duplicate_columns_count": len(dup_cols),
        }

    async def get_outliers(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate outlier detection results."""
        df = await self._load_dataframe(dataset_id)
        return OutlierDetector.detect_all(df)

    async def get_correlation(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate correlation analysis."""
        df = await self._load_dataframe(dataset_id)
        return CorrelationEngine.analyze(df)

    async def get_distribution(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate distribution analysis."""
        df = await self._load_dataframe(dataset_id)
        return DistributionAnalyzer.analyze(df)

    async def get_quality(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate data quality insights."""
        df = await self._load_dataframe(dataset_id)
        return QualityInsights.generate(df)

    async def get_insights(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate business insights and recommendations."""
        df = await self._load_dataframe(dataset_id)
        return QualityInsights.generate(df)

    async def get_visualizations(self, dataset_id: UUID) -> dict[str, Any]:
        """Generate JSON-ready visualization data."""
        df = await self._load_dataframe(dataset_id)
        return VisualizationGenerator.generate_all(df)

    async def run_full_analysis(self, dataset_id: UUID) -> dict[str, Any]:
        """Run the complete EDA pipeline and return all results."""
        start = time.perf_counter()
        logger.info("Full EDA analysis started for dataset: %s", dataset_id)

        df = await self._load_dataframe(dataset_id)

        result: dict[str, Any] = {
            "dataset_id": str(dataset_id),
            "summary": ProfilingEngine.generate_summary(df),
            "profile": ProfilingEngine.profile_all_columns(df),
            "statistics": {
                "numeric": {},
                "categorical": {},
            },
            "missing": {},
            "outliers": OutlierDetector.detect_all(df),
            "correlation": CorrelationEngine.analyze(df),
            "distribution": DistributionAnalyzer.analyze(df),
            "quality": QualityInsights.generate(df),
            "visualizations": VisualizationGenerator.generate_all(df),
        }

        from app.validators.type_detector import TypeDetector
        for col in df.columns:
            col_type = TypeDetector.detect_series_type(df[col])
            if col_type in ("integer", "float"):
                result["statistics"]["numeric"][str(col)] = NumericalAnalyzer.analyze(df[col])
            elif col_type in ("categorical", "string", "boolean"):
                result["statistics"]["categorical"][str(col)] = CategoricalAnalyzer.analyze(df[col])

        elapsed = round((time.perf_counter() - start) * 1000, 2)
        result["processing_time_ms"] = elapsed
        logger.info("Full EDA analysis completed for dataset: %s (%0.1f ms)", dataset_id, elapsed)
        return result