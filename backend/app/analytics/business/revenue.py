"""Revenue analytics module."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.exceptions import ValidationError


class RevenueAnalytics:
    """Computes revenue-level business metrics."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        required = {"order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")
        if df.empty:
            raise ValidationError("Dataset is empty.")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        total_revenue = float(result["revenue"].sum())
        result["month"] = result["order_date"].dt.to_period("M").astype(str)
        result["quarter"] = result["order_date"].dt.to_period("Q").astype(str)

        monthly = result.groupby("month")["revenue"].sum()
        quarterly = result.groupby("quarter")["revenue"].sum()
        monthly_series = monthly.sort_index()

        growth = {}
        if len(monthly_series) >= 2:
            pct = monthly_series.pct_change().dropna() * 100
            growth = {str(k): round(float(v), 2) for k, v in pct.items()}

        revenue_by_customer = {}
        if "customer_id" in result.columns:
            rev = result.groupby("customer_id")["revenue"].sum().nlargest(10)
            revenue_by_customer = {str(k): round(float(v), 2) for k, v in rev.items()}

        revenue_by_region = {}
        if "region" in result.columns:
            rev = result.groupby("region")["revenue"].sum().nlargest(10)
            revenue_by_region = {str(k): round(float(v), 2) for k, v in rev.items()}

        revenue_by_product = {}
        if "product_id" in result.columns:
            rev = result.groupby("product_id")["revenue"].sum().nlargest(10)
            revenue_by_product = {str(k): round(float(v), 2) for k, v in rev.items()}

        return {
            "total_revenue": round(total_revenue, 2),
            "gross_revenue": round(total_revenue, 2),
            "net_revenue": round(total_revenue, 2),
            "monthly_revenue": {k: round(v, 2) for k, v in monthly.items()},
            "quarterly_revenue": {k: round(v, 2) for k, v in quarterly.items()},
            "revenue_growth": growth,
            "revenue_by_customer": revenue_by_customer,
            "revenue_by_region": revenue_by_region,
            "revenue_by_product": revenue_by_product,
        }