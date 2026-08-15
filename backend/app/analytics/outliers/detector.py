"""Outlier detection using IQR, Z-score, and Modified Z-score methods."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class OutlierDetector:
    """Detects outliers using multiple statistical methods."""

    @classmethod
    def detect_all(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Run all outlier detection methods across numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        results: dict[str, Any] = {}

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue
            results[str(col)] = {
                "iqr": cls.detect_iqr(series),
                "zscore": cls.detect_zscore(series),
                "modified_zscore": cls.detect_modified_zscore(series),
            }

        total_outliers = sum(r["iqr"]["count"] for r in results.values())
        total_rows = len(df)
        return {
            "columns_analyzed": list(results.keys()),
            "results": results,
            "total_outliers": total_outliers,
            "affected_rows_pct": round(total_outliers / max(total_rows * len(results), 1) * 100, 2),
        }

    @classmethod
    def detect_iqr(cls, series: pd.Series) -> dict[str, Any]:
        """Detect outliers using the IQR method."""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return {"count": 0, "pct": 0.0, "method": "iqr", "lower_bound": float(q1), "upper_bound": float(q3)}
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = (series < lower) | (series > upper)
        return {
            "count": int(outliers.sum()),
            "pct": round(float(outliers.mean() * 100), 2),
            "method": "iqr",
            "lower_bound": round(float(lower), 4),
            "upper_bound": round(float(upper), 4),
        }

    @classmethod
    def detect_zscore(cls, series: pd.Series, threshold: float = 3.0) -> dict[str, Any]:
        """Detect outliers using Z-score method."""
        std = series.std()
        if std == 0:
            return {"count": 0, "pct": 0.0, "method": "zscore", "threshold": threshold}
        z_scores = np.abs(stats.zscore(series))
        outliers = z_scores > threshold
        return {
            "count": int(outliers.sum()),
            "pct": round(float(outliers.mean() * 100), 2),
            "method": "zscore",
            "threshold": threshold,
        }

    @classmethod
    def detect_modified_zscore(cls, series: pd.Series, threshold: float = 3.5) -> dict[str, Any]:
        """Detect outliers using Modified Z-score (MAD-based)."""
        median = series.median()
        mad = np.median(np.abs(series - median))
        if mad == 0:
            return {"count": 0, "pct": 0.0, "method": "modified_zscore", "threshold": threshold}
        modified_z = 0.6745 * (series - median) / mad
        outliers = np.abs(modified_z) > threshold
        return {
            "count": int(outliers.sum()),
            "pct": round(float(outliers.mean() * 100), 2),
            "method": "modified_zscore",
            "threshold": threshold,
        }