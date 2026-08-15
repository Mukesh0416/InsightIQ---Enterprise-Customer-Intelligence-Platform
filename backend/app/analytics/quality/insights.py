"""Data quality insights and business recommendation generator."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.validators.type_detector import TypeDetector


class QualityInsights:
    """Generates automated data quality and business insights."""

    @classmethod
    def generate(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate comprehensive quality insights and recommendations."""
        insights: list[dict[str, str]] = []
        recommendations: list[dict[str, str]] = []

        cls._check_missing_values(df, insights, recommendations)
        cls._check_duplicates(df, insights, recommendations)
        cls._check_constant_columns(df, insights, recommendations)
        cls._check_cardinality(df, insights, recommendations)
        cls._check_mixed_types(df, insights, recommendations)
        cls._check_negative_values(df, insights, recommendations)
        cls._check_correlations(df, insights, recommendations)
        cls._check_encoding_needs(df, recommendations)
        cls._check_scaling_needs(df, recommendations)
        cls._check_feature_engineering(df, recommendations)

        return {
            "quality_issues": insights,
            "recommendations": recommendations,
            "total_issues": len(insights),
            "total_recommendations": len(recommendations),
        }

    @classmethod
    def _check_missing_values(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        for col in df.columns:
            missing_pct = (df[col].isna().mean() * 100)
            if missing_pct > 50:
                insights.append({
                    "type": "high_missing",
                    "severity": "critical",
                    "column": str(col),
                    "message": f"Column '{col}' has {missing_pct:.1f}% missing values.",
                })
                recommendations.append({
                    "type": "drop_or_impute",
                    "column": str(col),
                    "message": f"Consider dropping '{col}' or using advanced imputation.",
                })
            elif missing_pct > 20:
                insights.append({
                    "type": "moderate_missing",
                    "severity": "warning",
                    "column": str(col),
                    "message": f"Column '{col}' has {missing_pct:.1f}% missing values.",
                })
            elif missing_pct > 0:
                insights.append({
                    "type": "missing_values",
                    "severity": "info",
                    "column": str(col),
                    "message": f"Column '{col}' has {missing_pct:.1f}% missing values.",
                })

    @classmethod
    def _check_duplicates(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            insights.append({
                "type": "duplicate_rows",
                "severity": "warning",
                "message": f"Found {dup_count} duplicate rows ({dup_count / len(df) * 100:.1f}%).",
            })
            recommendations.append({
                "type": "deduplication",
                "message": "Remove duplicate rows before analysis.",
            })

    @classmethod
    def _check_constant_columns(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        for col in df.columns:
            if df[col].nunique() == 1:
                insights.append({
                    "type": "constant_column",
                    "severity": "warning",
                    "column": str(col),
                    "message": f"Column '{col}' has zero variance (constant value).",
                })
                recommendations.append({
                    "type": "drop_constant",
                    "column": str(col),
                    "message": f"Drop '{col}' — it provides no information.",
                })

    @classmethod
    def _check_cardinality(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        for col in df.columns:
            nunique = df[col].nunique()
            total = len(df)
            if nunique / max(total, 1) > 0.95 and df[col].dtype == object:
                insights.append({
                    "type": "high_cardinality",
                    "severity": "info",
                    "column": str(col),
                    "message": f"Column '{col}' has very high cardinality ({nunique} unique).",
                })
            if nunique == 2:
                recommendations.append({
                    "type": "binary_encoding",
                    "column": str(col),
                    "message": f"'{col}' is binary — use label encoding.",
                })

    @classmethod
    def _check_mixed_types(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        for col in df.columns:
            if df[col].dtype == object:
                non_null = df[col].dropna()
                types = set()
                for val in non_null.head(100):
                    if isinstance(val, (int, float)):
                        types.add("numeric")
                    elif isinstance(val, str):
                        types.add("string")
                    elif isinstance(val, bool):
                        types.add("boolean")
                if len(types) > 1:
                    insights.append({
                        "type": "mixed_types",
                        "severity": "warning",
                        "column": str(col),
                        "message": f"Column '{col}' contains mixed data types: {types}.",
                    })

    @classmethod
    def _check_negative_values(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if (df[col] < 0).any():
                insights.append({
                    "type": "negative_values",
                    "severity": "info",
                    "column": str(col),
                    "message": f"Column '{col}' contains negative values.",
                })

    @classmethod
    def _check_correlations(
        cls, df: pd.DataFrame, insights: list, recommendations: list
    ) -> None:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] >= 2:
            corr = numeric_df.corr().abs()
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = float(corr.iloc[i, j])
                    if val > 0.8:
                        insights.append({
                            "type": "strong_correlation",
                            "severity": "warning",
                            "message": f"'{cols[i]}' and '{cols[j]}' are highly correlated ({val:.2f}).",
                        })
                        recommendations.append({
                            "type": "remove_redundant",
                            "message": f"Consider removing one of '{cols[i]}' or '{cols[j]}' to reduce multicollinearity.",
                        })

    @classmethod
    def _check_encoding_needs(cls, df: pd.DataFrame, recommendations: list) -> None:
        for col in df.columns:
            col_type = TypeDetector.detect_series_type(df[col])
            if col_type in ("categorical", "string") and df[col].nunique() <= 50:
                recommendations.append({
                    "type": "encoding",
                    "column": str(col),
                    "message": f"Encode '{col}' using one-hot or label encoding.",
                })

    @classmethod
    def _check_scaling_needs(cls, df: pd.DataFrame, recommendations: list) -> None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            std = df[col].std()
            mean = df[col].mean()
            if std > 0 and abs(mean) > 100:
                recommendations.append({
                    "type": "scaling",
                    "column": str(col),
                    "message": f"Scale '{col}' — values range widely (std={std:.1f}).",
                })

    @classmethod
    def _check_feature_engineering(cls, df: pd.DataFrame, recommendations: list) -> None:
        for col in df.columns:
            col_type = TypeDetector.detect_series_type(df[col])
            if col_type in ("date", "datetime"):
                recommendations.append({
                    "type": "feature_engineering",
                    "column": str(col),
                    "message": f"Extract year, month, day, weekday from '{col}'.",
                })