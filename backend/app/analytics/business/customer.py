"""Customer analytics module for enterprise business intelligence."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.exceptions import ValidationError

REQUIRED_COLUMNS = {"customer_id", "order_date", "revenue"}


class CustomerAnalytics:
    """Computes customer-level business metrics."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate comprehensive customer analytics."""
        cls._validate(df)
        df = cls._prepare(df)

        total_customers = int(df["customer_id"].nunique())
        total_orders = int(len(df))
        total_revenue = float(df["revenue"].sum())

        # Customer-level aggregation
        customer_stats = df.groupby("customer_id").agg(
            order_count=("order_id", "count") if "order_id" in df.columns else ("revenue", "count"),
            total_spend=("revenue", "sum"),
            first_order=("order_date", "min"),
            last_order=("order_date", "max"),
        ).reset_index()

        now = df["order_date"].max()
        customer_stats["recency_days"] = (now - customer_stats["last_order"]).dt.days
        customer_stats["customer_age_days"] = (customer_stats["last_order"] - customer_stats["first_order"]).dt.days

        # New vs returning
        new_customers = int((customer_stats["order_count"] == 1).sum())
        returning_customers = total_customers - new_customers

        # Active = ordered within last 90 days
        active_customers = int((customer_stats["recency_days"] <= 90).sum())
        inactive_customers = total_customers - active_customers

        # Repeat purchase rate
        repeat_purchase_rate = round(returning_customers / max(total_customers, 1) * 100, 2)

        # Churn rate (customers not active in last 90 days)
        churn_rate = round(inactive_customers / max(total_customers, 1) * 100, 2)

        # Average metrics
        avg_customer_value = round(total_revenue / max(total_customers, 1), 2)
        avg_order_frequency = round(total_orders / max(total_customers, 1), 2)
        avg_basket_size = round(total_revenue / max(total_orders, 1), 2)

        # Growth rate (compare first half vs second half)
        growth_rate = cls._compute_growth_rate(df)

        return {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "returning_customers": returning_customers,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
            "customer_growth_rate": growth_rate,
            "average_customer_value": avg_customer_value,
            "average_order_frequency": avg_order_frequency,
            "average_basket_size": avg_basket_size,
            "repeat_purchase_rate": repeat_purchase_rate,
            "customer_churn_rate": churn_rate,
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
        }

    @classmethod
    def _validate(cls, df: pd.DataFrame) -> None:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")
        if df.empty:
            raise ValidationError("Dataset is empty.")

    @classmethod
    def _prepare(cls, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])
        if "order_id" not in result.columns:
            result["order_id"] = range(1, len(result) + 1)
        return result

    @classmethod
    def _compute_growth_rate(cls, df: pd.DataFrame) -> float:
        if len(df) < 2:
            return 0.0
        midpoint = df["order_date"].min() + (df["order_date"].max() - df["order_date"].min()) / 2
        first_half = df[df["order_date"] <= midpoint]["customer_id"].nunique()
        second_half = df[df["order_date"] > midpoint]["customer_id"].nunique()
        if first_half == 0:
            return 100.0
        return round((second_half - first_half) / first_half * 100, 2)