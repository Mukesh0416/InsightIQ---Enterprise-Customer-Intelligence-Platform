"""Distribution analysis: normal, skewed, uniform detection."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class DistributionAnalyzer:
    """Detects and classifies data distributions."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze distributions for all numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        results: dict[str, Any] = {}

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 8:
                results[str(col)] = {"type": "insufficient_data"}
                continue
            results[str(col)] = cls._analyze_series(series)

        return {"columns": results}

    @classmethod
    def _analyze_series(cls, series: pd.Series) -> dict[str, Any]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            skewness = float(stats.skew(series, nan_policy="omit", bias=False))
            kurtosis = float(stats.kurtosis(series, nan_policy="omit", fisher=False, bias=False))

        dist_type = cls._classify_distribution(series, skewness, kurtosis)

        return {
            "type": dist_type,
            "skewness": round(skewness, 4),
            "kurtosis": round(kurtosis, 4),
            "is_normal": cls._test_normality(series),
            "is_uniform": cls._test_uniformity(series),
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std_dev": round(float(series.std()), 4),
        }

    @classmethod
    def _classify_distribution(cls, series: pd.Series, skewness: float, kurtosis: float) -> str:
        if cls._test_normality(series):
            return "normal"
        if cls._test_uniformity(series):
            return "uniform"
        if skewness > 1:
            return "right_skewed"
        if skewness < -1:
            return "left_skewed"
        if kurtosis > 3:
            return "leptokurtic"
        if kurtosis < 0:
            return "platykurtic"
        return "approximately_symmetric"

    @classmethod
    def _test_normality(cls, series: pd.Series) -> bool:
        try:
            _, p_value = stats.shapiro(series.head(5000))
            return p_value > 0.05
        except Exception:
            return False

    @classmethod
    def _test_uniformity(cls, series: pd.Series) -> bool:
        try:
            _, p_value = stats.kstest(
                (series - series.min()) / (series.max() - series.min() + 1e-10),
                "uniform",
            )
            return p_value > 0.05
        except Exception:
            return False