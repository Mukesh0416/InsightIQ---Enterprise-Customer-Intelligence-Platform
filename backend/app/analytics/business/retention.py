"""Retention and CLV analytics modules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.exceptions import ValidationError


class RetentionAnalytics:
    """Computes customer retention and lifetime value metrics."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        required = {"customer_id", "order_date"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")
        if df.empty:
            raise ValidationError("Dataset is empty.")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result = result.dropna(subset=["order_date"])

        customer_stats = result.groupby("customer_id").agg(
            order_count=("order_date", "count"),
            first_order=("order_date", "min"),
            last_order=("order_date", "max"),
        ).reset_index()

        now = result["order_date"].max()
        customer_stats["days_since_last"] = (now - customer_stats["last_order"]).dt.days
        customer_stats["customer_age_days"] = (customer_stats["last_order"] - customer_stats["first_order"]).dt.days

        total_customers = len(customer_stats)
        repeat = int((customer_stats["order_count"] >= 2).sum())
        active_90 = int((customer_stats["days_since_last"] <= 90).sum())
        reactivated = int(
            ((customer_stats["customer_age_days"] >= 180) & (customer_stats["days_since_last"] <= 90)).sum()
        )

        return {
            "total_customers": total_customers,
            "retention_rate": round(active_90 / max(total_customers, 1) * 100, 2),
            "repeat_purchase_rate": round(repeat / max(total_customers, 1) * 100, 2),
            "customer_survival_rate": round(active_90 / max(total_customers, 1) * 100, 2),
            "customer_reactivation_rate": round(reactivated / max(total_customers, 1) * 100, 2),
            "average_customer_age_days": round(float(customer_stats["customer_age_days"].mean()), 2),
        }

    @classmethod
    def compute_clv(cls, df: pd.DataFrame) -> dict[str, Any]:
        """Compute Customer Lifetime Value metrics."""
        required = {"customer_id", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)

        customer_rev = result.groupby("customer_id")["revenue"].sum()
        avg_clv = float(customer_rev.mean()) if len(customer_rev) else 0.0
        top_clv = customer_rev.nlargest(10)

        return {
            "historical_clv": round(float(customer_rev.sum()), 2),
            "average_clv": round(avg_clv, 2),
            "predictive_clv": round(avg_clv, 2),
            "top_clv_customers": {str(k): round(float(v), 2) for k, v in top_clv.items()},
            "total_customers": int(len(customer_rev)),
        }


class RFMAnalyzer:
    """Computes Recency, Frequency, Monetary (RFM) analysis and segments."""

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> dict[str, Any]:
        required = {"customer_id", "order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        now = result["order_date"].max()
        rfm = result.groupby("customer_id").agg(
            recency=("order_date", lambda x: (now - x.max()).days),
            frequency=("order_date", "count"),
            monetary=("revenue", "sum"),
        )

        # Quantile-based scoring (1-5)
        rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
        rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
        rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
        rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)

        # Segment assignment
        def segment(row: pd.Series) -> str:
            if row["r_score"] >= 4 and row["f_score"] >= 4 and row["m_score"] >= 4:
                return "Champions"
            if row["r_score"] >= 4 and row["f_score"] >= 3 and row["m_score"] >= 3:
                return "Loyal Customers"
            if row["r_score"] >= 4 and row["f_score"] <= 2:
                return "New Customers"
            if row["r_score"] >= 3 and row["f_score"] >= 4:
                return "Potential Loyalists"
            if row["r_score"] <= 2 and row["f_score"] >= 3:
                return "At Risk"
            if row["r_score"] <= 2 and row["f_score"] <= 2:
                return "Lost Customers"
            if row["r_score"] >= 3 and row["f_score"] >= 2 and row["m_score"] <= 2:
                return "Need Attention"
            return "Hibernating"

        rfm["segment"] = rfm.apply(segment, axis=1)
        segment_counts = rfm["segment"].value_counts().to_dict()

        return {
            "total_customers": int(len(rfm)),
            "segments": {k: int(v) for k, v in segment_counts.items()},
            "segment_distribution": {
                k: round(v / len(rfm) * 100, 2) for k, v in segment_counts.items()
            },
            "average_recency_days": round(float(rfm["recency"].mean()), 2),
            "average_frequency": round(float(rfm["frequency"].mean()), 2),
            "average_monetary": round(float(rfm["monetary"].mean()), 2),
        }


class CohortAnalyzer:
    """Computes monthly/weekly customer cohort retention matrices."""

    @classmethod
    def analyze(cls, df: pd.DataFrame, period: str = "M") -> dict[str, Any]:
        required = {"customer_id", "order_date", "revenue"}
        missing = required - set(df.columns)
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")

        result = df.copy()
        result["order_date"] = pd.to_datetime(result["order_date"], errors="coerce")
        result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce").fillna(0)
        result = result.dropna(subset=["order_date"])

        # Define cohort period
        freq = "M" if period == "monthly" else "W"
        result["cohort"] = result.groupby("customer_id")["order_date"].transform("min").dt.to_period(freq)
        result["period"] = result["order_date"].dt.to_period(freq)
        result["cohort_index"] = (result["period"] - result["cohort"]).apply(lambda x: x.n)

        # Retention matrix
        cohort_data = result.groupby(["cohort", "cohort_index"])["customer_id"].nunique().unstack().fillna(0)
        retention_matrix = {}
        for idx, row in cohort_data.iterrows():
            first = row.iloc[0] if len(row) > 0 else 0
            retention_matrix[str(idx)] = {
                str(col): round(float(row[col]) / max(float(first), 1) * 100, 2)
                for col in row.index
            }

        # Revenue matrix
        rev_data = result.groupby(["cohort", "cohort_index"])["revenue"].sum().unstack().fillna(0)
        revenue_matrix = {
            str(idx): {str(col): round(float(val), 2) for col, val in row.items()}
            for idx, row in rev_data.iterrows()
        }

        # Repeat purchase matrix
        repeat_data = result.groupby(["cohort", "cohort_index"])["order_id" if "order_id" in result.columns else "customer_id"].count().unstack().fillna(0)
        repeat_matrix = {
            str(idx): {str(col): int(val) for col, val in row.items()}
            for idx, row in repeat_data.iterrows()
        }

        return {
            "period": period,
            "retention_matrix": retention_matrix,
            "revenue_matrix": revenue_matrix,
            "repeat_purchase_matrix": repeat_matrix,
            "cohorts": [str(c) for c in cohort_data.index],
        }