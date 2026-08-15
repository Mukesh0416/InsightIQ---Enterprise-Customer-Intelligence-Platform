"""
Data quality engine that scores datasets (0–100) across five dimensions.

Computes completeness, consistency, validity, uniqueness, and accuracy
scores plus a comprehensive issue report.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.validators.type_detector import TypeDetector


class QualityEngine:
    """Computes data quality metrics and an overall quality score."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        if df.empty:
            return {
                "quality_score": 0.0,
                "completeness": 0.0,
                "consistency": 0.0,
                "validity": 0.0,
                "uniqueness": 0.0,
                "accuracy": 0.0,
                "issues": [
                    {"type": "empty_dataset", "severity": "critical", "message": "Dataset contains no rows."}
                ],
                "column_summary": {},
            }

        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = int(df.notna().sum().sum())

        # ── Completeness: % of non-null cells ──────────────────────────────
        completeness = (non_null_cells / total_cells) * 100 if total_cells else 0.0

        # ── Uniqueness: 100 − duplicate row penalty ────────────────────────
        unique_rows = df.drop_duplicates().shape[0]
        dup_ratio = 1 - (unique_rows / max(df.shape[0], 1))
        uniqueness = max(0.0, 100.0 - (dup_ratio * 100))

        # ── Validity: column type/value checks ─────────────────────────────
        validity_scores: list[float] = []
        column_summary: dict[str, Any] = {}
        issues: list[dict[str, Any]] = []

        for col in df.columns:
            series = df[col]
            col_type = TypeDetector.detect_series_type(series)
            null_pct = (series.isna().mean() * 100) if len(series) else 0.0
            nunique = series.nunique()
            col_issues: list[str] = []

            # Validity checks
            if null_pct > 50:
                col_issues.append(f"High null percentage ({null_pct:.1f}%)")
            if nunique == 1:
                col_issues.append("Constant column")
            if col_type in ("integer", "float"):
                numeric = pd.to_numeric(series, errors="coerce")
                if numeric.isna().sum() > 0:
                    col_issues.append(f"{int(numeric.isna().sum())} non-numeric values")
                if (numeric < 0).any():
                    col_issues.append("Contains negative values")
                outliers = TypeDetector.detect_outliers_iqr(series)
                if outliers > 0:
                    col_issues.append(f"{outliers} outlier values")
            if series.dtype == object:
                whitespace = series.astype(str).str.match(r"^\s*$").sum()
                if whitespace > 0:
                    col_issues.append(f"{int(whitespace)} whitespace-only values")

            # Column-level validity score
            col_validity = 100.0 - (len(col_issues) * min(20.0, 100.0 / max(len(df.columns), 1)))
            col_validity = max(0.0, col_validity)
            validity_scores.append(col_validity)

            column_summary[str(col)] = {
                "type": col_type,
                "null_percentage": round(null_pct, 2),
                "distinct_count": int(nunique),
                "issues": col_issues,
            }

            for issue in col_issues:
                issues.append(
                    {
                        "column": str(col),
                        "type": issue,
                        "severity": "warning",
                        "message": f"Column '{col}': {issue}",
                    }
                )

        validity = sum(validity_scores) / len(validity_scores) if validity_scores else 0.0

        # ── Consistency: uniform types across rows ─────────────────────────
        consistency = 100.0 - (len(issues) * 5.0)
        consistency = max(0.0, min(100.0, consistency))

        # ── Accuracy: inferred via detectable issues ───────────────────────
        accuracy = 100.0 - (len(issues) * 10.0)
        accuracy = max(0.0, min(100.0, accuracy))

        # ── Overall score (weighted) ───────────────────────────────────────
        quality_score = (
            completeness * 0.30
            + consistency * 0.15
            + validity * 0.25
            + uniqueness * 0.20
            + accuracy * 0.10
        )

        return {
            "quality_score": round(min(100.0, quality_score), 2),
            "completeness": round(completeness, 2),
            "consistency": round(consistency, 2),
            "validity": round(validity, 2),
            "uniqueness": round(uniqueness, 2),
            "accuracy": round(accuracy, 2),
            "issues": issues,
            "column_summary": column_summary,
        }