"""KPI engine and trend analysis modules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.exceptions import ValidationError


class KPIEngine:
    """Computes executive-level KPI metrics."""

    @classmethod
    def compute(cls, df: pd.DataFrame) -> dict[str, Any]:
        required = {"customer_id", "order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        total_revenue = float(result["revenue"].sum())
        total_customers = int(result["customer_id"].nunique())
        total_orders = int(len(result))
        months_span = max(int(result["order_date"].dt.to_period("M").nunique()), 1)

        # Arpu
        arpu = round(total_revenue / max(total_customers, 1), 2)

        # AOV
        aov = round(total_revenue / max(total_orders, 1), 2)

        # Churn (last 90 days)
        now = result["order_date"].max()
        last_order = result.groupby("customer_id")["order_date"].max()
        churned = int((last_order < (now - pd.Timedelta(days=90))).sum())
        churn_rate = round(churned / max(total_customers, 1) * 100, 2)

        # Retention
        active = total_customers - churned
        retention_rate = round(active / max(total_customers, 1) * 100, 2)

        # Revenue growth (last month vs previous)
        monthly = result.groupby(result["order_date"].dt.to_period("M"))["revenue"].sum().sort_index()
        revenue_growth = 0.0
        if len(monthly) >= 2:
            last_month = float(monthly.iloc[-1])
            prev_month = float(monthly.iloc[-2])
            if prev_month != 0:
                revenue_growth = round((last_month - prev_month) / prev_month * 100, 2)

        # Customer growth
        by_month = result.groupby(result["order_date"].dt.to_period("M"))["customer_id"].nunique()
        customer_growth = 0.0
        if len(by_month) >= 2:
            if by_month.iloc[-2] != 0:
                customer_growth = round((by_month.iloc[-1] - by_month.iloc[-2]) / by_month.iloc[-2] * 100, 2)

        repeat_customers = int(result.groupby("customer_id")["order_date"].count()[lambda x: x > 1].count())
        conversion_rate = round(repeat_customers / max(total_customers, 1) * 100, 2)

        return {
            "total_revenue": round(total_revenue, 2),
            "total_customers": total_customers,
            "total_orders": total_orders,
            "arpu": arpu,
            "average_order_value": aov,
            "churn_rate": churn_rate,
            "retention_rate": retention_rate,
            "conversion_rate": conversion_rate,
            "revenue_growth_pct": revenue_growth,
            "customer_growth_pct": customer_growth,
            "net_revenue_growth_pct": revenue_growth,
            "monthly_average_revenue": round(total_revenue / months_span, 2),
        }


class TrendAnalyzer:
    """Computes trend analysis across time periods."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        required = {"order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        monthly = result.groupby(result["order_date"].dt.to_period("M"))["revenue"].sum().sort_index()
        quarterly = result.groupby(result["order_date"].dt.to_period("Q"))["revenue"].sum().sort_index()
        yearly = result.groupby(result["order_date"].dt.year)["revenue"].sum().sort_index()

        # MoM growth
        mom = monthly.pct_change().dropna() * 100
        # QoQ growth
        qoq = quarterly.pct_change().dropna() * 100
        # YoY growth
        yoy = yearly.pct_change().dropna() * 100

        # Moving average (3-month)
        moving_avg = monthly.rolling(3, min_periods=1).mean()

        return {
            "monthly_series": {str(k): round(float(v), 2) for k, v in monthly.items()},
            "quarterly_series": {str(k): round(float(v), 2) for k, v in quarterly.items()},
            "yearly_series": {str(k): round(float(v), 2) for k, v in yearly.items()},
            "month_over_month": {str(k): round(float(v), 2) for k, v in mom.items()},
            "quarter_over_quarter": {str(k): round(float(v), 2) for k, v in qoq.items()},
            "year_over_year": {str(k): round(float(v), 2) for k, v in yoy.items()},
            "moving_average_3m": {str(k): round(float(v), 2) for k, v in moving_avg.items()},
            "growth_periods": {
                "total_periods": int(len(monthly)),
                "growth_periods": int((mom > 0).sum()),
                "decline_periods": int((mom < 0).sum()),
            },
        }