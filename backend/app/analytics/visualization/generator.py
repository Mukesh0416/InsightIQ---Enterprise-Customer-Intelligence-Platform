"""Visualization data generator for JSON-ready chart data."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class VisualizationGenerator:
    """Generates JSON-serializable data for frontend charting libraries."""

    @classmethod
    def generate_all(cls, df: pd.DataFrame) -> dict[str, Any]:
        return {
            "histograms": cls._generate_histograms(df),
            "bar_charts": cls._generate_bar_charts(df),
            "pie_charts": cls._generate_pie_charts(df),
            "box_plots": cls._generate_box_plots(df),
            "scatter_plots": cls._generate_scatter_plots(df),
            "correlation_heatmap": cls._generate_correlation_heatmap(df),
            "missing_heatmap": cls._generate_missing_heatmap(df),
        }

    @classmethod
    def _generate_histograms(cls, df: pd.DataFrame) -> dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result: dict[str, Any] = {}
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            counts, bin_edges = np.histogram(series, bins=min(30, len(series)))
            result[str(col)] = {
                "bins": [round(float(b), 4) for b in bin_edges],
                "counts": [int(c) for c in counts],
            }
        return result

    @classmethod
    def _generate_bar_charts(cls, df: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in df.columns:
            if df[col].dtype == object or df[col].nunique() <= 20:
                vc = df[col].value_counts().head(15)
                result[str(col)] = {
                    "labels": [str(k) for k in vc.index],
                    "values": [int(v) for v in vc.values],
                }
        return result

    @classmethod
    def _generate_pie_charts(cls, df: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for col in df.columns:
            if df[col].dtype == object and df[col].nunique() <= 10:
                vc = df[col].value_counts()
                result[str(col)] = {
                    "labels": [str(k) for k in vc.index],
                    "values": [int(v) for v in vc.values],
                }
        return result

    @classmethod
    def _generate_box_plots(cls, df: pd.DataFrame) -> dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result: dict[str, Any] = {}
        for col in numeric_cols:
            s = df[col].dropna()
            if len(s) == 0:
                continue
            result[str(col)] = {
                "min": round(float(s.min()), 4),
                "q1": round(float(s.quantile(0.25)), 4),
                "median": round(float(s.median()), 4),
                "q3": round(float(s.quantile(0.75)), 4),
                "max": round(float(s.max()), 4),
            }
        return result

    @classmethod
    def _generate_scatter_plots(cls, df: pd.DataFrame) -> list[dict[str, Any]]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        plots: list[dict[str, Any]] = []
        if len(numeric_cols) < 2:
            return plots
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                common = df[[numeric_cols[i], numeric_cols[j]]].dropna()
                if len(common) == 0:
                    continue
                sample = common.head(1000)
                plots.append({
                    "x_column": str(numeric_cols[i]),
                    "y_column": str(numeric_cols[j]),
                    "x": [round(float(v), 4) for v in sample[numeric_cols[i]]],
                    "y": [round(float(v), 4) for v in sample[numeric_cols[j]]],
                })
        return plots[:10]

    @classmethod
    def _generate_correlation_heatmap(cls, df: pd.DataFrame) -> dict[str, Any]:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return {"columns": [], "matrix": []}
        corr = numeric_df.corr()
        return {
            "columns": [str(c) for c in corr.columns],
            "matrix": [[round(float(v), 4) for v in row] for row in corr.values],
        }

    @classmethod
    def _generate_missing_heatmap(cls, df: pd.DataFrame) -> dict[str, Any]:
        missing = df.isna()
        cols = [str(c) for c in df.columns]
        sample = missing.head(100)
        matrix = [[int(v) for v in row] for row in sample.values]
        return {
            "columns": cols,
            "matrix": matrix,
            "missing_pct": {
                str(c): round(float(df[c].isna().mean() * 100), 2)
                for c in df.columns
            },
        }