"""Numerical statistical analysis for numeric columns."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class NumericalAnalyzer:
    """Computes detailed numerical statistics for numeric columns."""

    @classmethod
    def analyze(cls, series: pd.Series) -> dict[str, Any]:
        """Generate comprehensive numerical statistics."""
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if len(numeric) == 0:
            return {"error": "No numeric values found."}

        q1 = float(numeric.quantile(0.25))
        q3 = float(numeric.quantile(0.75))
        mean = float(numeric.mean())
        std = float(numeric.std()) if len(numeric) > 1 else 0.0

        return {
            "mean": round(mean, 4),
            "median": round(float(numeric.median()), 4),
            "mode": float(numeric.mode().iloc[0]) if len(numeric.mode()) > 0 else None,
            "variance": round(float(numeric.var()), 4) if len(numeric) > 1 else 0.0,
            "std_dev": round(std, 4),
            "percentiles": {
                "p1": round(float(numeric.quantile(0.01)), 4),
                "p5": round(float(numeric.quantile(0.05)), 4),
                "p10": round(float(numeric.quantile(0.10)), 4),
                "p25": round(q1, 4),
                "p50": round(float(numeric.median()), 4),
                "p75": round(q3, 4),
                "p90": round(float(numeric.quantile(0.90)), 4),
                "p95": round(float(numeric.quantile(0.95)), 4),
                "p99": round(float(numeric.quantile(0.99)), 4),
            },
            "quartiles": {"q1": round(q1, 4), "q2": round(float(numeric.median()), 4), "q3": round(q3, 4)},
            "coefficient_of_variation": round(std / mean, 4) if mean != 0 else None,
            "outlier_count": cls._count_outliers_iqr(numeric),
            "outlier_pct": round(cls._count_outliers_iqr(numeric) / len(numeric) * 100, 2),
            "distribution_type": cls._detect_distribution(numeric),
            "min": float(numeric.min()),
            "max": float(numeric.max()),
            "range": round(float(numeric.max() - numeric.min()), 4),
            "sum": round(float(numeric.sum()), 4),
            "count": int(len(numeric)),
        }

    @classmethod
    def _count_outliers_iqr(cls, numeric: pd.Series) -> int:
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return 0
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return int(((numeric < lower) | (numeric > upper)).sum())

    @classmethod
    def _detect_distribution(cls, numeric: pd.Series) -> str:
        if len(numeric) < 8:
            return "insufficient_data"
        try:
            stat, p_value = stats.shapiro(numeric.head(5000))
            if p_value > 0.05:
                return "normal"
        except Exception:
            pass
        skewness = float(stats.skew(numeric))
        if skewness > 1:
            return "right_skewed"
        if skewness < -1:
            return "left_skewed"
        if abs(skewness) < 0.5:
            return "approximately_symmetric"
        return "moderately_skewed"