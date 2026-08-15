"""
Data profiling engine for generating dataset summaries and column profiles.

Computes comprehensive statistical profiles for any pandas DataFrame,
including dataset-level metrics and per-column statistics.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from app.validators.type_detector import TypeDetector

logger = logging.getLogger(__name__)


class ProfilingEngine:
    """Generates complete statistical profiles for datasets."""

    @classmethod
    def generate_summary(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate a high-level dataset summary."""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        duplicate_cols = cls._find_duplicate_columns(df)
        memory_bytes = int(df.memory_usage(deep=True).sum())

        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "memory_usage_bytes": memory_bytes,
            "memory_usage_mb": round(memory_bytes / (1024 * 1024), 2),
            "missing_cells": missing_cells,
            "missing_cells_pct": round((missing_cells / total_cells * 100) if total_cells else 0, 2),
            "duplicate_rows": duplicate_rows,
            "duplicate_rows_pct": round((duplicate_rows / max(df.shape[0], 1) * 100), 2),
            "duplicate_columns": duplicate_cols,
            "duplicate_columns_count": len(duplicate_cols),
            "dataset_size_bytes": memory_bytes,
            "column_names": [str(c) for c in df.columns],
        }

    @classmethod
    def profile_column(cls, series: pd.Series) -> dict[str, Any]:
        """Generate a complete statistical profile for a single column."""
        col_name = str(series.name)
        col_type = TypeDetector.detect_series_type(series)
        non_null = series.dropna()
        total = len(series)
        missing = int(series.isna().sum())
        unique = int(series.nunique())

        profile: dict[str, Any] = {
            "name": col_name,
            "type": col_type,
            "nullable": missing > 0,
            "unique_count": unique,
            "distinct_pct": round((unique / max(total, 1) * 100), 2),
            "missing_count": missing,
            "missing_pct": round((missing / max(total, 1) * 100), 2),
            "duplicate_count": total - unique - missing,
            "duplicate_pct": round(((total - unique - missing) / max(total, 1) * 100), 2),
        }

        if col_type in ("integer", "float"):
            profile.update(cls._numeric_stats(non_null))
        elif col_type in ("categorical", "string", "boolean"):
            profile.update(cls._categorical_stats(non_null))
        elif col_type in ("date", "datetime"):
            profile.update(cls._date_stats(non_null))
        elif col_type in ("email", "phone", "uuid"):
            profile.update(cls._text_stats(non_null))

        profile["entropy"] = cls._compute_entropy(non_null)
        return profile

    @classmethod
    def profile_all_columns(cls, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Profile every column in the DataFrame."""
        return [cls.profile_column(df[col]) for col in df.columns]

    @classmethod
    def _numeric_stats(cls, series: pd.Series) -> dict[str, Any]:
        if len(series) == 0:
            return {}
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if len(numeric) == 0:
            return {}
        q1 = float(numeric.quantile(0.25))
        q3 = float(numeric.quantile(0.75))
        iqr = q3 - q1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            skewness = float(stats.skew(numeric, nan_policy="omit", bias=False)) if len(numeric) > 2 else 0.0
            kurtosis = float(stats.kurtosis(numeric, nan_policy="omit", fisher=False, bias=False)) if len(numeric) > 3 else 0.0

        return {
            "minimum": float(numeric.min()),
            "maximum": float(numeric.max()),
            "mean": round(float(numeric.mean()), 4),
            "median": round(float(numeric.median()), 4),
            "mode": float(numeric.mode().iloc[0]) if len(numeric.mode()) > 0 else None,
            "std_dev": round(float(numeric.std()), 4) if len(numeric) > 1 else 0.0,
            "variance": round(float(numeric.var()), 4) if len(numeric) > 1 else 0.0,
            "skewness": round(skewness, 4),
            "kurtosis": round(kurtosis, 4),
            "range": round(float(numeric.max() - numeric.min()), 4),
            "iqr": round(iqr, 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "percentiles": {
                "p5": round(float(numeric.quantile(0.05)), 4),
                "p10": round(float(numeric.quantile(0.10)), 4),
                "p25": round(q1, 4),
                "p50": round(float(numeric.median()), 4),
                "p75": round(q3, 4),
                "p90": round(float(numeric.quantile(0.90)), 4),
                "p95": round(float(numeric.quantile(0.95)), 4),
                "p99": round(float(numeric.quantile(0.99)), 4),
            },
            "coefficient_of_variation": round(
                float(numeric.std() / numeric.mean()), 4
            ) if numeric.mean() != 0 else None,
        }

    @classmethod
    def _categorical_stats(cls, series: pd.Series) -> dict[str, Any]:
        if len(series) == 0:
            return {}
        value_counts = series.value_counts()
        top_categories = value_counts.head(10).to_dict()
        cardinality = int(series.nunique())
        rare_threshold = max(1, len(series) * 0.01)
        rare = value_counts[value_counts < rare_threshold]
        return {
            "unique_values": cardinality,
            "top_categories": {str(k): int(v) for k, v in top_categories.items()},
            "frequency_table": {str(k): int(v) for k, v in value_counts.head(20).items()},
            "mode": str(series.mode().iloc[0]) if len(series.mode()) > 0 else None,
            "cardinality": cardinality,
            "rare_categories_count": int(len(rare)),
            "category_distribution": {
                str(k): round(int(v) / len(series) * 100, 2)
                for k, v in value_counts.head(10).items()
            },
        }

    @classmethod
    def _date_stats(cls, series: pd.Series) -> dict[str, Any]:
        if len(series) == 0:
            return {}
        try:
            dates = pd.to_datetime(series, errors="coerce").dropna()
        except Exception:
            return {}
        if len(dates) == 0:
            return {}
        now = pd.Timestamp.now(tz=dates.dt.tz) if dates.dt.tz else pd.Timestamp.now()
        return {
            "date_range_start": str(dates.min()),
            "date_range_end": str(dates.max()),
            "missing_dates": int(series.isna().sum()),
            "future_dates": int((dates > now).sum()),
            "historical_range_days": int((dates.max() - dates.min()).days),
            "granularity": cls._detect_granularity(dates),
        }

    @classmethod
    def _text_stats(cls, series: pd.Series) -> dict[str, Any]:
        if len(series) == 0:
            return {}
        str_series = series.astype(str)
        lengths = str_series.str.len()
        return {
            "average_length": round(float(lengths.mean()), 2),
            "max_length": int(lengths.max()),
            "min_length": int(lengths.min()),
            "empty_strings": int((str_series == "").sum()),
            "whitespace_count": int(str_series.str.match(r"^\s+$").sum()),
            "special_characters": int(str_series.str.contains(r"[^a-zA-Z0-9\s]").sum()),
        }

    @classmethod
    def _compute_entropy(cls, series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return round(float(entropy), 4)

    @classmethod
    def _detect_granularity(cls, dates: pd.Series) -> str:
        if len(dates) < 2:
            return "unknown"
        diffs = dates.sort_values().diff().dropna()
        if diffs.empty:
            return "unknown"
        median_diff = diffs.median()
        if median_diff <= pd.Timedelta(hours=1):
            return "hourly"
        if median_diff <= pd.Timedelta(days=1):
            return "daily"
        if median_diff <= pd.Timedelta(days=7):
            return "weekly"
        if median_diff <= pd.Timedelta(days=31):
            return "monthly"
        return "yearly"

    @classmethod
    def _find_duplicate_columns(cls, df: pd.DataFrame) -> list[str]:
        dup_cols: list[str] = []
        cols = df.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                if df[cols[i]].equals(df[cols[j]]):
                    dup_cols.append(str(cols[j]))
        return dup_cols