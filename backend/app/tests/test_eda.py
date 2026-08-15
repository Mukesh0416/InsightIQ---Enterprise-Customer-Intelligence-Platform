"""
Unit tests for the EDA analytics engine modules.

Tests profiling, statistics, outlier detection, correlation,
distribution analysis, quality insights, and visualization generation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.analytics.correlation.engine import CorrelationEngine
from app.analytics.distribution.analyzer import DistributionAnalyzer
from app.analytics.outliers.detector import OutlierDetector
from app.analytics.profiling.engine import ProfilingEngine
from app.analytics.quality.insights import QualityInsights
from app.analytics.statistics.categorical import CategoricalAnalyzer
from app.analytics.statistics.numerical import NumericalAnalyzer
from app.analytics.visualization.generator import VisualizationGenerator


@pytest.fixture
def sample_df() -> pd.DataFrame:
    np.random.seed(42)
    return pd.DataFrame({
        "id": range(1, 101),
        "age": np.random.randint(18, 80, 100),
        "salary": np.random.normal(50000, 15000, 100).round(2),
        "category": np.random.choice(["A", "B", "C"], 100),
        "score": np.random.uniform(0, 100, 100).round(1),
        "constant": [1] * 100,
    })


@pytest.fixture
def df_with_missing() -> pd.DataFrame:
    return pd.DataFrame({
        "a": [1, 2, None, 4, 5],
        "b": ["x", None, "z", "x", "y"],
        "c": [1.1, 2.2, 3.3, None, 5.5],
    })


@pytest.fixture
def df_with_outliers() -> pd.DataFrame:
    return pd.DataFrame({"values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]})


class TestProfilingEngine:
    def test_generate_summary(self, sample_df: pd.DataFrame) -> None:
        summary = ProfilingEngine.generate_summary(sample_df)
        assert summary["rows"] == 100
        assert summary["columns"] == 6
        assert summary["missing_cells"] == 0
        assert len(summary["column_names"]) == 6

    def test_profile_column_numeric(self, sample_df: pd.DataFrame) -> None:
        profile = ProfilingEngine.profile_column(sample_df["age"])
        assert profile["type"] in ("integer", "float")
        assert "mean" in profile and "median" in profile
        assert "skewness" in profile and "entropy" in profile

    def test_profile_column_categorical(self, sample_df: pd.DataFrame) -> None:
        profile = ProfilingEngine.profile_column(sample_df["category"])
        assert profile["type"] in ("categorical", "string")
        assert "top_categories" in profile and "cardinality" in profile

    def test_profile_all_columns(self, sample_df: pd.DataFrame) -> None:
        profiles = ProfilingEngine.profile_all_columns(sample_df)
        assert len(profiles) == 6

    def test_duplicate_columns_detection(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [4, 5, 6]})
        dups = ProfilingEngine._find_duplicate_columns(df)
        assert "b" in dups


class TestNumericalAnalyzer:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = NumericalAnalyzer.analyze(sample_df["salary"])
        assert "mean" in result and "percentiles" in result
        assert "outlier_count" in result and "distribution_type" in result

    def test_empty_series(self) -> None:
        result = NumericalAnalyzer.analyze(pd.Series([], dtype=float))
        assert "error" in result


class TestCategoricalAnalyzer:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = CategoricalAnalyzer.analyze(sample_df["category"])
        assert result["unique_values"] == 3
        assert "frequency_table" in result and "mode" in result

    def test_empty_series(self) -> None:
        result = CategoricalAnalyzer.analyze(pd.Series([], dtype=object))
        assert "error" in result


class TestOutlierDetector:
    def test_detect_iqr(self, df_with_outliers: pd.DataFrame) -> None:
        result = OutlierDetector.detect_iqr(df_with_outliers["values"])
        assert result["count"] > 0 and result["method"] == "iqr"

    def test_detect_zscore(self, df_with_outliers: pd.DataFrame) -> None:
        result = OutlierDetector.detect_zscore(df_with_outliers["values"])
        assert result["count"] > 0 and result["method"] == "zscore"

    def test_detect_all(self, sample_df: pd.DataFrame) -> None:
        result = OutlierDetector.detect_all(sample_df)
        assert "columns_analyzed" in result and "total_outliers" in result


class TestCorrelationEngine:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = CorrelationEngine.analyze(sample_df)
        assert "pearson" in result and "spearman" in result
        assert "kendall" in result and "vif" in result

    def test_insufficient_columns(self) -> None:
        result = CorrelationEngine.analyze(pd.DataFrame({"a": [1, 2, 3]}))
        assert "error" in result


class TestDistributionAnalyzer:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = DistributionAnalyzer.analyze(sample_df)
        assert "columns" in result and "age" in result["columns"]

    def test_normal_distribution(self) -> None:
        np.random.seed(42)
        normal_data = pd.DataFrame({"x": np.random.normal(0, 1, 1000)})
        result = DistributionAnalyzer.analyze(normal_data)
        assert result["columns"]["x"]["type"] in ("normal", "approximately_symmetric")


class TestQualityInsights:
    def test_generate(self, sample_df: pd.DataFrame) -> None:
        result = QualityInsights.generate(sample_df)
        assert "quality_issues" in result and "recommendations" in result

    def test_constant_column_detected(self, sample_df: pd.DataFrame) -> None:
        result = QualityInsights.generate(sample_df)
        constant = [i for i in result["quality_issues"] if i["type"] == "constant_column"]
        assert len(constant) > 0 and constant[0]["column"] == "constant"

    def test_missing_values_detected(self, df_with_missing: pd.DataFrame) -> None:
        result = QualityInsights.generate(df_with_missing)
        missing = [i for i in result["quality_issues"] if "missing" in i["type"]]
        assert len(missing) > 0


class TestVisualizationGenerator:
    def test_generate_all(self, sample_df: pd.DataFrame) -> None:
        result = VisualizationGenerator.generate_all(sample_df)
        assert "histograms" in result and "bar_charts" in result
        assert "box_plots" in result and "correlation_heatmap" in result

    def test_histograms(self, sample_df: pd.DataFrame) -> None:
        hists = VisualizationGenerator._generate_histograms(sample_df)
        assert "age" in hists and "bins" in hists["age"]

    def test_box_plots(self, sample_df: pd.DataFrame) -> None:
        boxes = VisualizationGenerator._generate_box_plots(sample_df)
        assert "age" in boxes and "median" in boxes["age"]

    def test_correlation_heatmap(self, sample_df: pd.DataFrame) -> None:
        heatmap = VisualizationGenerator._generate_correlation_heatmap(sample_df)
        assert "columns" in heatmap and "matrix" in heatmap

    def test_missing_heatmap(self, df_with_missing: pd.DataFrame) -> None:
        heatmap = VisualizationGenerator._generate_missing_heatmap(df_with_missing)
        assert "columns" in heatmap and "missing_pct" in heatmap