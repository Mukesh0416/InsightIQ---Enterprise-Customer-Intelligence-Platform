"""Categorical statistical analysis for categorical/string columns."""

from __future__ import annotations

from typing import Any

import pandas as pd


class CategoricalAnalyzer:
    """Computes detailed statistics for categorical columns."""

    @classmethod
    def analyze(cls, series: pd.Series) -> dict[str, Any]:
        """Generate comprehensive categorical statistics."""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {"error": "No values found."}

        value_counts = non_null.value_counts()
        cardinality = int(non_null.nunique())
        total = len(non_null)

        return {
            "unique_values": cardinality,
            "top_categories": {str(k): int(v) for k, v in value_counts.head(10).items()},
            "frequency_table": {str(k): int(v) for k, v in value_counts.head(30).items()},
            "mode": str(non_null.mode().iloc[0]) if len(non_null.mode()) > 0 else None,
            "cardinality": cardinality,
            "cardinality_ratio": round(cardinality / total, 4),
            "rare_categories": cls._find_rare_categories(value_counts, total),
            "rare_categories_count": int(len(cls._find_rare_categories(value_counts, total))),
            "category_distribution": {
                str(k): round(int(v) / total * 100, 2)
                for k, v in value_counts.head(15).items()
            },
            "count": int(total),
        }

    @classmethod
    def _find_rare_categories(cls, value_counts: pd.Series, total: int) -> dict[str, int]:
        threshold = max(1, total * 0.01)
        rare = value_counts[value_counts < threshold]
        return {str(k): int(v) for k, v in rare.head(20).items()}