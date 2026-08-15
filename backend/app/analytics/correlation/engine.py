"""Correlation analysis engine: Pearson, Spearman, Kendall, and VIF."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class CorrelationEngine:
    """Computes correlation matrices and multicollinearity metrics."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate complete correlation analysis for numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if numeric_df.shape[1] < 2:
            return {"error": "Need at least 2 numeric columns for correlation."}

        return {
            "pearson": cls._pearson(numeric_df),
            "spearman": cls._spearman(numeric_df),
            "kendall": cls._kendall(numeric_df),
            "highly_correlated": cls._find_highly_correlated(numeric_df),
            "vif": cls._compute_vif(numeric_df),
        }

    @classmethod
    def _pearson(cls, df: pd.DataFrame) -> dict[str, Any]:
        corr = df.corr(method="pearson")
        return {
            "matrix": corr.round(4).to_dict(),
            "columns": list(corr.columns),
        }

    @classmethod
    def _spearman(cls, df: pd.DataFrame) -> dict[str, Any]:
        corr = df.corr(method="spearman")
        return {
            "matrix": corr.round(4).to_dict(),
            "columns": list(corr.columns),
        }

    @classmethod
    def _kendall(cls, df: pd.DataFrame) -> dict[str, Any]:
        corr = df.corr(method="kendall")
        return {
            "matrix": corr.round(4).to_dict(),
            "columns": list(corr.columns),
        }

    @classmethod
    def _find_highly_correlated(cls, df: pd.DataFrame, threshold: float = 0.8) -> list[dict[str, Any]]:
        corr = df.corr(method="pearson").abs()
        pairs: list[dict[str, Any]] = []
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = float(corr.iloc[i, j])
                if val >= threshold:
                    pairs.append({
                        "column_1": str(cols[i]),
                        "column_2": str(cols[j]),
                        "correlation": round(val, 4),
                    })
        return pairs

    @classmethod
    def _compute_vif(cls, df: pd.DataFrame) -> dict[str, float]:
        """Compute Variance Inflation Factor for each numeric column."""
        from sklearn.linear_model import LinearRegression

        vif_results: dict[str, float] = {}
        cols = df.columns
        for i, col in enumerate(cols):
            y = df[col].values
            X = df.drop(columns=[col]).values
            if X.shape[1] == 0:
                vif_results[str(col)] = float("inf")
                continue
            try:
                model = LinearRegression()
                model.fit(X, y)
                r_squared = model.score(X, y)
                if r_squared >= 1.0:
                    vif_results[str(col)] = float("inf")
                else:
                    vif_results[str(col)] = round(1.0 / (1.0 - r_squared), 4)
            except Exception:
                vif_results[str(col)] = float("inf")
        return vif_results