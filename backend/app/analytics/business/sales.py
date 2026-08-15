"""Sales analytics module."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.exceptions import ValidationError


class SalesAnalytics:
    """Computes sales-level business metrics."""

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

        total_sales = float(result["revenue"].sum())
        total_orders = int(len(result))

        # Average Order Value
        aov = round(total_sales / max(total_orders, 1), 2)

        # Top products
        top_products: list[dict[str, Any]] = []
        if "product_id" in result.columns:
            product_data = result.groupby("product_id").agg(
                revenue=("revenue", "sum"),
                orders=("revenue", "count"),
            ).reset_index().sort_values("revenue", ascending=False).head(10)
            top_products = product_data.to_dict(orient="records")

        # Top customers
        top_customers: list[dict[str, Any]] = []
        if "customer_id" in result.columns:
            customer_data = result.groupby("customer_id").agg(
                revenue=("revenue", "sum"),
                orders=("revenue", "count"),
            ).reset_index().sort_values("revenue", ascending=False).head(10)
            top_customers = customer_data.to_dict(orient="records")

        # Daily / monthly breakdown
        result["month"] = result["order_date"].dt.to_period("M").astype(str)
        result["day"] = result["order_date"].dt.date.astype(str)
        monthly = result.groupby("month")["revenue"].sum().to_dict()
        daily = result.groupby("day")["revenue"].sum().to_dict()

        return {
            "total_sales": round(total_sales, 2),
            "total_orders": total_orders,
            "average_order_value": aov,
            "monthly_sales": {str(k): round(float(v), 2) for k, v in monthly.items()},
            "daily_sales": {str(k): round(float(v), 2) for k, v in daily.items()},
            "top_products": top_products,
            "top_customers": top_customers,
        }