"""Business recommendation and insights engines."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates intelligent business recommendations."""

    @classmethod
    def generate(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate business insights and recommendations."""
        required = {"customer_id", "order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        now = result["order_date"].max()

        # Customer-level features
        customer = result.groupby("customer_id").agg(
            frequency=("order_date", "count"),
            monetary=("revenue", "sum"),
            last_order=("order_date", "max"),
        )
        customer["recency_days"] = (now - customer["last_order"]).dt.days

        # High-value customers to retain (high spend, at risk of inactivity)
        high_value_at_risk = customer[
            (customer["monetary"] >= customer["monetary"].quantile(0.75))
            & (customer["recency_days"] > 45)
            & (customer["recency_days"] <= 90)
        ].nlargest(10, "monetary")

        # Customers at risk (high recency)
        at_risk = customer[
            (customer["recency_days"] > 90)
            & (customer["recency_days"] <= 180)
            & (customer["frequency"] >= 2)
        ].nlargest(10, "monetary")

        # Upsell opportunities (high frequency, moderate monetary)
        upsell = customer[
            (customer["frequency"] >= customer["frequency"].quantile(0.75))
            & (customer["monetary"] < customer["monetary"].quantile(0.5))
        ].nlargest(10, "frequency")

        # Cross-sell opportunities (product affinity if products exist)
        cross_sell: dict[str, Any] = {}
        if "product_id" in result.columns:
            product_pair = result.groupby(["customer_id", "product_id"]).size().reset_index(name="count")
            multi_product = product_pair.groupby("customer_id").filter(lambda x: len(x) >= 2)
            cross_sell = {
                "customers_with_multi_products": int(multi_product["customer_id"].nunique()),
                "products_per_customer_avg": round(float(product_pair.groupby("customer_id")["product_id"].nunique().mean()), 2),
            }

        recommendations: list[dict[str, Any]] = []

        # High-value retention
        for cid, row in high_value_at_risk.iterrows():
            recommendations.append({
                "type": "retain_high_value",
                "priority": "high",
                "customer_id": str(cid),
                "message": f"High-value customer {cid} (${row['monetary']:.2f}) may churn in {row['recency_days']:.0f} days.",
            })

        # At-risk customers
        for cid, row in at_risk.iterrows():
            recommendations.append({
                "type": "win_back",
                "priority": "medium",
                "customer_id": str(cid),
                "message": f"Customer {cid} has been inactive for {row['recency_days']:.0f} days.",
            })

        # Upsell
        for cid, row in upsell.iterrows():
            recommendations.append({
                "type": "upsell",
                "priority": "medium",
                "customer_id": str(cid),
                "message": f"Frequent customer {cid} (orders={int(row['frequency'])}) is a good upsell target.",
            })

        # Revenue optimization
        if cross_sell:
            recommendations.append({
                "type": "cross_sell",
                "priority": "medium",
                "message": f"Cross-sell opportunity: {cross_sell['customers_with_multi_products']} customers buy multiple products.",
            })

        recommendations.append({
            "type": "engagement",
            "priority": "low",
            "message": "Average customer recency is "
            f"{round(float(customer['recency_days'].mean()), 1)} days — implement re-engagement campaigns.",
        })

        return {
            "recommendations": recommendations[:20],
            "total_recommendations": len(recommendations),
            "high_value_at_risk": {str(k): round(float(v["monetary"]), 2) for k, v in high_value_at_risk.iterrows()},
            "customers_at_risk": {str(k): round(float(v["recency_days"]), 1) for k, v in at_risk.iterrows()},
            "cross_sell_data": cross_sell,
        }


class ExecutiveSummaryEngine:
    """Generates executive summary report data."""

    @classmethod
    def generate(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Generate an executive summary of business performance."""
        from app.analytics.business.kpi import KPIEngine
        from app.analytics.business.customer import CustomerAnalytics
        from app.analytics.business.revenue import RevenueAnalytics

        try:
            kpis = KPIEngine.compute(df)
            customers = CustomerAnalytics.analyze(df)
            revenue = RevenueAnalytics.analyze(df)
        except ValidationError:
            return {"error": "Unable to generate executive summary."}

        total_customers = kpis["total_customers"]
        total_revenue = kpis["total_revenue"]
        churn_rate = kpis["churn_rate"]
        retention_rate = kpis["retention_rate"]
        growth = kpis["revenue_growth_pct"]

        return {
            "summary": {
                "total_customers": total_customers,
                "total_revenue": total_revenue,
                "average_revenue_per_user": kpis["arpu"],
                "revenue_growth_pct": growth,
                "churn_rate": churn_rate,
                "retention_rate": retention_rate,
            },
            "key_findings": [
                f"Revenue is {growth:.1f}% {'up' if growth >= 0 else 'down'} over the last period.",
                f"Customer retention rate is {retention_rate:.1f}%.",
                f"Churn rate is {churn_rate:.1f}% — {'manageable' if churn_rate < 20 else 'needs attention'}.",
            ],
            "risks": [
                {"type": "revenue_risk", "severity": "low" if growth >= 0 else "high"},
                {"type": "customer_risk", "severity": "low" if churn_rate < 20 else "high"},
                {"type": "retention_risk", "severity": "low" if retention_rate >= 60 else "medium"},
            ],
            "opportunities": cls._find_opportunities(df, customers),
        }

    @classmethod
    def _find_opportunities(cls, df: pd.DataFrame, customers: dict[str, Any]) -> list[dict[str, str]]:
        opportunities: list[dict[str, str]] = []
        if customers["repeat_purchase_rate"] < 30:
            opportunities.append({
                "type": "repeat_purchases",
                "message": "Increase repeat purchase rate with loyalty programs.",
            })
        if customers["inactive_customers"] > 0.2 * customers["total_customers"]:
            opportunities.append({
                "type": "reactivation",
                "message": f"Re-activate {customers['inactive_customers']} inactive customers.",
            })
        return opportunities