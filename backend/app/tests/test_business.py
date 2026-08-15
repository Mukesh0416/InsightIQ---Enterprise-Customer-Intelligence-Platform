"""
Unit tests for the Business Analytics Engine modules.

Tests customer, sales, revenue, retention, RFM, cohort, CLV,
KPI, trend, recommendation, and executive summary analytics.
"""

from __future__ import annotations

import importlib

import numpy as np
import pandas as pd
import pytest

from app.analytics.business.customer import CustomerAnalytics
from app.analytics.business.kpi import KPIEngine, TrendAnalyzer
from app.analytics.business.recommendations import ExecutiveSummaryEngine, RecommendationEngine
from app.analytics.business.retention import CohortAnalyzer, RetentionAnalytics, RFMAnalyzer
from app.analytics.business.revenue import RevenueAnalytics
from app.exceptions import ValidationError

try:
    sales_module = importlib.import_module("app.analytics.business.sales")
    SalesAnalytics = sales_module.SalesAnalytics
except (ImportError, AttributeError):
    class SalesAnalytics:  # type: ignore[no-redef]
        @staticmethod
        def analyze(df: pd.DataFrame) -> dict:
            raise NotImplementedError("SalesAnalytics is unavailable in this environment.")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    customers = np.random.randint(1, 51, n)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    revenue = np.random.uniform(10, 500, n).round(2)
    products = np.random.choice(["P001", "P002", "P003", "P004"], n)
    categories = np.random.choice(["Electronics", "Clothing", "Home"], n)
    regions = np.random.choice(["North", "South", "East", "West"], n)
    channels = np.random.choice(["Online", "Retail"], n)
    return pd.DataFrame({
        "customer_id": customers,
        "order_id": range(1, n + 1),
        "order_date": dates,
        "revenue": revenue,
        "product_id": products,
        "category": categories,
        "region": regions,
        "channel": channels,
    })


@pytest.fixture
def df_missing_columns() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3]})


class TestCustomerAnalytics:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = CustomerAnalytics.analyze(sample_df)
        assert result["total_customers"] == 50
        assert result["total_orders"] == 500
        assert result["new_customers"] > 0
        assert result["returning_customers"] > 0
        assert "customer_growth_rate" in result
        assert "average_customer_value" in result
        assert "repeat_purchase_rate" in result
        assert "customer_churn_rate" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            CustomerAnalytics.analyze(df_missing_columns)

    def test_empty_dataset(self) -> None:
        with pytest.raises(ValidationError):
            CustomerAnalytics.analyze(pd.DataFrame(columns=["customer_id", "order_date", "revenue"]))


class TestSalesAnalytics:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = SalesAnalytics.analyze(sample_df)
        assert result["total_sales"] > 0
        assert result["total_orders"] == 500
        assert "monthly_sales" in result
        assert "daily_sales" in result
        assert "yearly_sales" in result
        assert "sales_growth" in result
        assert "average_order_value" in result
        assert "top_products" in result
        assert "top_customers" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            SalesAnalytics.analyze(df_missing_columns)


class TestRevenueAnalytics:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = RevenueAnalytics.analyze(sample_df)
        assert result["total_revenue"] > 0
        assert "gross_revenue" in result
        assert "net_revenue" in result
        assert "monthly_revenue" in result
        assert "quarterly_revenue" in result
        assert "revenue_growth" in result
        assert "revenue_by_customer" in result
        assert "revenue_by_region" in result
        assert "revenue_by_product" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            RevenueAnalytics.analyze(df_missing_columns)


class TestRetentionAnalytics:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = RetentionAnalytics.analyze(sample_df)
        assert result["total_customers"] == 50
        assert "retention_rate" in result
        assert "repeat_purchase_rate" in result
        assert "customer_survival_rate" in result
        assert "customer_reactivation_rate" in result
        assert "average_customer_age_days" in result

    def test_clv(self, sample_df: pd.DataFrame) -> None:
        result = RetentionAnalytics.compute_clv(sample_df)
        assert result["historical_clv"] > 0
        assert result["average_clv"] > 0
        assert result["predictive_clv"] > 0
        assert "top_clv_customers" in result
        assert result["total_customers"] == 50

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            RetentionAnalytics.analyze(df_missing_columns)


class TestRFMAnalyzer:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = RFMAnalyzer.analyze(sample_df)
        assert result["total_customers"] == 50
        assert "segments" in result
        assert "segment_distribution" in result
        assert "average_recency_days" in result
        assert "average_frequency" in result
        assert "average_monetary" in result
        assert len(result["segments"]) > 0

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            RFMAnalyzer.analyze(df_missing_columns)


class TestCohortAnalyzer:
    def test_analyze_monthly(self, sample_df: pd.DataFrame) -> None:
        result = CohortAnalyzer.analyze(sample_df, "monthly")
        assert result["period"] == "monthly"
        assert "retention_matrix" in result
        assert "revenue_matrix" in result
        assert "repeat_purchase_matrix" in result
        assert "cohorts" in result

    def test_analyze_weekly(self, sample_df: pd.DataFrame) -> None:
        result = CohortAnalyzer.analyze(sample_df, "weekly")
        assert result["period"] == "weekly"

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            CohortAnalyzer.analyze(df_missing_columns)


class TestKPIEngine:
    def test_compute(self, sample_df: pd.DataFrame) -> None:
        result = KPIEngine.compute(sample_df)
        assert result["total_revenue"] > 0
        assert result["total_customers"] == 50
        assert result["total_orders"] == 500
        assert "arpu" in result
        assert "average_order_value" in result
        assert "churn_rate" in result
        assert "retention_rate" in result
        assert "conversion_rate" in result
        assert "revenue_growth_pct" in result
        assert "customer_growth_pct" in result
        assert "net_revenue_growth_pct" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            KPIEngine.compute(df_missing_columns)


class TestTrendAnalyzer:
    def test_analyze(self, sample_df: pd.DataFrame) -> None:
        result = TrendAnalyzer.analyze(sample_df)
        assert "monthly_series" in result
        assert "quarterly_series" in result
        assert "yearly_series" in result
        assert "month_over_month" in result
        assert "quarter_over_quarter" in result
        assert "year_over_year" in result
        assert "moving_average_3m" in result
        assert "growth_periods" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            TrendAnalyzer.analyze(df_missing_columns)


class TestRecommendationEngine:
    def test_generate(self, sample_df: pd.DataFrame) -> None:
        result = RecommendationEngine.generate(sample_df)
        assert "recommendations" in result
        assert "total_recommendations" in result
        assert "high_value_at_risk" in result
        assert "customers_at_risk" in result
        assert "cross_sell_data" in result

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        with pytest.raises(ValidationError):
            RecommendationEngine.generate(df_missing_columns)


class TestExecutiveSummaryEngine:
    def test_generate(self, sample_df: pd.DataFrame) -> None:
        result = ExecutiveSummaryEngine.generate(sample_df)
        assert "summary" in result
        assert "key_findings" in result
        assert "risks" in result
        assert "opportunities" in result
        assert result["summary"]["total_customers"] == 50

    def test_missing_columns(self, df_missing_columns: pd.DataFrame) -> None:
        result = ExecutiveSummaryEngine.generate(df_missing_columns)
        assert "error" in result
