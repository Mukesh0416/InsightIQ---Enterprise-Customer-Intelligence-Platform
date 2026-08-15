"""
Business AI Use Cases.

Implements domain-specific ML services:
  - Customer Churn Prediction
  - Customer Segmentation
  - Revenue Forecasting
  - Customer Lifetime Value Prediction
  - Sales Forecasting
  - Product Recommendation (architecture foundation)
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

_REQUIRED = {
    "churn": ["customer_id", "order_date", "revenue"],
    "segmentation": ["customer_id", "order_date", "revenue"],
    "clv": ["customer_id", "order_date", "revenue"],
    "forecasting": ["order_date", "revenue"],
}


def _validate(df: pd.DataFrame, use_case: str) -> None:
    missing = [c for c in _REQUIRED[use_case] if c not in df.columns]
    if missing:
        raise ValidationError(f"Missing columns for {use_case}: {missing}")
    if df.empty:
        raise ValidationError("Dataset is empty.")


def _build_rfm(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Build RFM features per customer."""
    ref = reference_date or df["order_date"].max()
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    rfm = df.groupby("customer_id").agg(
        recency=("order_date", lambda x: (ref - x.max()).days),
        frequency=("order_id" if "order_id" in df.columns else "order_date", "count"),
        monetary=("revenue", "sum"),
    ).reset_index()
    return rfm


class ChurnPredictionService:
    """
    Customer Churn Prediction.

    Builds RFM features and trains a gradient boosting classifier
    to predict churn probability per customer.
    """

    @staticmethod
    def predict(df: pd.DataFrame, churn_days: int = 90) -> dict[str, Any]:
        """
        Predict churn probability for each customer.

        Args:
            df: Transaction DataFrame with customer_id, order_date, revenue.
            churn_days: Days of inactivity to label a customer as churned.

        Returns:
            Dict with per-customer churn scores and aggregate statistics.
        """
        _validate(df, "churn")
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        ref_date = df["order_date"].max()

        rfm = _build_rfm(df, ref_date)
        rfm["churned"] = (rfm["recency"] > churn_days).astype(int)

        if rfm["churned"].nunique() < 2:
            # All same class — return rule-based scores
            rfm["churn_probability"] = (rfm["recency"] / rfm["recency"].max()).round(4)
            rfm["churn_risk"] = pd.cut(rfm["churn_probability"], bins=[0, 0.3, 0.6, 1.0], labels=["low", "medium", "high"])
        else:
            X = rfm[["recency", "frequency", "monetary"]].values
            y = rfm["churned"].values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            probs = model.predict_proba(X_scaled)[:, 1]
            rfm["churn_probability"] = probs.round(4)
            rfm["churn_risk"] = pd.cut(probs, bins=[0, 0.3, 0.6, 1.0], labels=["low", "medium", "high"])

        churn_rate = float(rfm["churned"].mean())
        high_risk = rfm[rfm["churn_risk"] == "high"][["customer_id", "churn_probability", "recency"]].head(20)

        return {
            "total_customers": len(rfm),
            "churned_customers": int(rfm["churned"].sum()),
            "churn_rate": round(churn_rate, 4),
            "high_risk_customers": high_risk.to_dict(orient="records"),
            "risk_distribution": rfm["churn_risk"].value_counts().to_dict(),
            "avg_churn_probability": round(float(rfm["churn_probability"].mean()), 4),
            "customer_scores": rfm[["customer_id", "churn_probability", "churn_risk", "recency", "frequency", "monetary"]].to_dict(orient="records"),
        }


class CustomerSegmentationService:
    """
    Customer Segmentation using KMeans on RFM features.

    Assigns business-meaningful segment labels based on cluster centroids.
    """

    @staticmethod
    def segment(df: pd.DataFrame, n_segments: int = 5) -> dict[str, Any]:
        """
        Segment customers into behavioural groups.

        Returns:
            Dict with segment assignments, profiles, and distribution.
        """
        _validate(df, "segmentation")
        from sklearn.cluster import KMeans

        rfm = _build_rfm(df)
        scaler = StandardScaler()
        X = scaler.fit_transform(rfm[["recency", "frequency", "monetary"]])

        n_segments = min(n_segments, len(rfm) - 1)
        kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
        rfm["segment"] = kmeans.fit_predict(X)

        # Label segments by monetary value rank
        segment_profiles = rfm.groupby("segment").agg(
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            customer_count=("customer_id", "count"),
        ).reset_index()

        segment_profiles["rank"] = segment_profiles["avg_monetary"].rank(ascending=False).astype(int)
        label_map = {
            1: "Champions", 2: "Loyal Customers", 3: "Potential Loyalists",
            4: "At Risk", 5: "Lost Customers",
        }
        segment_profiles["label"] = segment_profiles["rank"].map(
            lambda r: label_map.get(r, f"Segment {r}")
        )
        seg_label_map = dict(zip(segment_profiles["segment"], segment_profiles["label"]))
        rfm["segment_label"] = rfm["segment"].map(seg_label_map)

        return {
            "total_customers": len(rfm),
            "n_segments": n_segments,
            "segment_profiles": segment_profiles.round(2).to_dict(orient="records"),
            "segment_distribution": rfm["segment_label"].value_counts().to_dict(),
            "customer_segments": rfm[["customer_id", "segment", "segment_label", "recency", "frequency", "monetary"]].to_dict(orient="records"),
        }


class CLVPredictionService:
    """
    Customer Lifetime Value Prediction.

    Computes historical CLV and predicts future CLV using a Ridge regression
    on RFM + tenure features.
    """

    @staticmethod
    def predict(df: pd.DataFrame, prediction_months: int = 12) -> dict[str, Any]:
        """
        Predict future CLV for each customer.

        Returns:
            Dict with historical CLV, predicted CLV, and top customers.
        """
        _validate(df, "clv")
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        ref_date = df["order_date"].max()

        rfm = _build_rfm(df, ref_date)
        first_order = df.groupby("customer_id")["order_date"].min().reset_index()
        first_order.columns = ["customer_id", "first_order"]
        rfm = rfm.merge(first_order, on="customer_id")
        rfm["tenure_days"] = (ref_date - rfm["first_order"]).dt.days.clip(lower=1)
        rfm["avg_order_value"] = rfm["monetary"] / rfm["frequency"].clip(lower=1)
        rfm["purchase_rate"] = rfm["frequency"] / (rfm["tenure_days"] / 30).clip(lower=1)

        # Historical CLV
        rfm["historical_clv"] = rfm["monetary"]

        # Predictive CLV: avg_order_value * purchase_rate * prediction_months
        rfm["predicted_clv"] = (rfm["avg_order_value"] * rfm["purchase_rate"] * prediction_months).round(2)

        # Refine with Ridge regression if enough data
        if len(rfm) >= 10:
            X = rfm[["recency", "frequency", "monetary", "tenure_days", "avg_order_value"]].values
            y = rfm["historical_clv"].values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            model = Ridge(alpha=1.0)
            model.fit(X_scaled, y)
            rfm["predicted_clv"] = np.maximum(model.predict(X_scaled) * (prediction_months / max(rfm["tenure_days"].mean() / 30, 1)), 0).round(2)

        top_clv = rfm.nlargest(20, "predicted_clv")[["customer_id", "historical_clv", "predicted_clv", "frequency", "monetary"]].to_dict(orient="records")

        return {
            "total_customers": len(rfm),
            "prediction_months": prediction_months,
            "total_historical_clv": round(float(rfm["historical_clv"].sum()), 2),
            "total_predicted_clv": round(float(rfm["predicted_clv"].sum()), 2),
            "avg_historical_clv": round(float(rfm["historical_clv"].mean()), 2),
            "avg_predicted_clv": round(float(rfm["predicted_clv"].mean()), 2),
            "top_clv_customers": top_clv,
            "clv_segments": {
                "high_value": int((rfm["predicted_clv"] > rfm["predicted_clv"].quantile(0.75)).sum()),
                "medium_value": int(((rfm["predicted_clv"] >= rfm["predicted_clv"].quantile(0.25)) & (rfm["predicted_clv"] <= rfm["predicted_clv"].quantile(0.75))).sum()),
                "low_value": int((rfm["predicted_clv"] < rfm["predicted_clv"].quantile(0.25)).sum()),
            },
        }


class RevenueForecastingService:
    """
    Revenue Forecasting using Ridge regression on time-series features.

    Generates monthly revenue forecasts with trend and seasonality components.
    """

    @staticmethod
    def forecast(df: pd.DataFrame, periods: int = 6) -> dict[str, Any]:
        """
        Forecast monthly revenue for the next N periods.

        Returns:
            Dict with historical series, forecast, and confidence intervals.
        """
        _validate(df, "forecasting")
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        monthly = df.set_index("order_date").resample("ME")["revenue"].sum().reset_index()
        monthly.columns = ["month", "revenue"]
        monthly = monthly.sort_values("month")

        if len(monthly) < 3:
            raise ValidationError("Need at least 3 months of data for forecasting.")

        # Build time features
        monthly["t"] = np.arange(len(monthly))
        monthly["month_num"] = monthly["month"].dt.month
        monthly["sin_season"] = np.sin(2 * np.pi * monthly["month_num"] / 12)
        monthly["cos_season"] = np.cos(2 * np.pi * monthly["month_num"] / 12)

        X = monthly[["t", "sin_season", "cos_season"]].values
        y = monthly["revenue"].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = Ridge(alpha=1.0)
        model.fit(X_scaled, y)

        # Forecast future periods
        last_t = monthly["t"].max()
        last_month = monthly["month"].max()
        future_months = pd.date_range(last_month + pd.offsets.MonthEnd(1), periods=periods, freq="ME")
        future_t = np.arange(last_t + 1, last_t + 1 + periods)
        future_month_nums = future_months.month
        future_X = np.column_stack([
            future_t,
            np.sin(2 * np.pi * future_month_nums / 12),
            np.cos(2 * np.pi * future_month_nums / 12),
        ])
        future_X_scaled = scaler.transform(future_X)
        forecast_values = model.predict(future_X_scaled)

        # Confidence interval (±1 std of residuals)
        residuals = y - model.predict(X_scaled)
        std_err = float(np.std(residuals))

        forecast = [
            {
                "month": str(m.date()),
                "forecast": round(max(float(v), 0), 2),
                "lower_bound": round(max(float(v) - 1.96 * std_err, 0), 2),
                "upper_bound": round(float(v) + 1.96 * std_err, 2),
            }
            for m, v in zip(future_months, forecast_values)
        ]

        return {
            "historical_revenue": [
                {"month": str(r["month"].date()), "revenue": round(float(r["revenue"]), 2)}
                for _, r in monthly.iterrows()
            ],
            "forecast": forecast,
            "periods": periods,
            "total_forecast_revenue": round(sum(f["forecast"] for f in forecast), 2),
            "avg_monthly_forecast": round(float(np.mean([f["forecast"] for f in forecast])), 2),
            "trend": "increasing" if forecast_values[-1] > forecast_values[0] else "decreasing",
        }


class SalesForecastingService:
    """Sales volume forecasting (order count) using the same time-series approach."""

    @staticmethod
    def forecast(df: pd.DataFrame, periods: int = 6) -> dict[str, Any]:
        """Forecast monthly order volume."""
        if "order_date" not in df.columns:
            raise ValidationError("Missing column: order_date")
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df["order_count"] = 1
        monthly = df.set_index("order_date").resample("ME")["order_count"].sum().reset_index()
        monthly.columns = ["month", "order_count"]
        # Reuse revenue forecasting logic with order_count as target
        monthly["revenue"] = monthly["order_count"]
        return RevenueForecastingService.forecast(monthly.rename(columns={"month": "order_date"}), periods=periods)


class ProductRecommendationService:
    """
    Product Recommendation Foundation.

    Architecture: item-based collaborative filtering skeleton.
    Full implementation requires user-item interaction matrix.
    """

    @staticmethod
    def get_architecture() -> dict[str, Any]:
        """Return the recommendation system architecture specification."""
        return {
            "approach": "collaborative_filtering",
            "algorithm": "item_based_cosine_similarity",
            "components": [
                "user_item_matrix_builder",
                "similarity_calculator",
                "candidate_generator",
                "ranking_model",
                "diversity_reranker",
            ],
            "data_requirements": ["customer_id", "product_id", "purchase_date", "quantity", "revenue"],
            "scalability": "Designed for Apache Spark / distributed matrix factorization at scale.",
            "status": "architecture_defined",
            "next_steps": [
                "Collect product_id and quantity columns in dataset",
                "Build user-item interaction matrix",
                "Train ALS or SVD model",
                "Deploy as real-time recommendation API",
            ],
        }

    @staticmethod
    def top_products_per_segment(df: pd.DataFrame) -> dict[str, Any]:
        """Return top products per customer segment as a recommendation foundation."""
        if "product_id" not in df.columns or "customer_id" not in df.columns:
            return {"error": "product_id and customer_id columns required."}

        top = (
            df.groupby(["product_id"])["revenue"]
            .agg(["sum", "count"])
            .reset_index()
            .rename(columns={"sum": "total_revenue", "count": "purchase_count"})
            .sort_values("total_revenue", ascending=False)
            .head(20)
        )
        return {
            "top_products": top.to_dict(orient="records"),
            "recommendation_basis": "popularity",
        }
