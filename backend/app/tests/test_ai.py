"""
Tests for the Enterprise AI Platform.

Covers feature engineering, feature selection, model training,
evaluation, explainability, drift detection, monitoring,
and business AI use cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from app.ai.drift.detector import DriftDetector
from app.ai.evaluation.evaluator import ModelEvaluator
from app.ai.feature_engineering.engine import FeatureEngineeringEngine
from app.ai.feature_selection.selector import FeatureSelector
from app.ai.monitoring.monitor import ModelMonitor
from app.ai.training.algorithms import default_algorithms, get_estimator
from app.ai.training.cross_validation import CrossValidator
from app.ai.training.hyperparameter_opt import HyperparameterOptimizer
from app.exceptions import ValidationError
from app.services.business_ai import (
    ChurnPredictionService,
    CLVPredictionService,
    CustomerSegmentationService,
    RevenueForecastingService,
    SalesForecastingService,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def clf_data() -> tuple[pd.DataFrame, pd.Series]:
    X, y = make_classification(n_samples=200, n_features=10, n_informative=5, random_state=42)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
    return df, pd.Series(y, name="target")


@pytest.fixture
def reg_data() -> tuple[pd.DataFrame, pd.Series]:
    X, y = make_regression(n_samples=200, n_features=10, n_informative=5, random_state=42)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
    return df, pd.Series(y, name="target")


@pytest.fixture
def transaction_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 300
    return pd.DataFrame({
        "customer_id": np.random.randint(1, 31, n),
        "order_id": range(1, n + 1),
        "order_date": pd.date_range("2023-01-01", periods=n, freq="D"),
        "revenue": np.random.uniform(10, 500, n).round(2),
        "product_id": np.random.choice(["P001", "P002", "P003"], n),
    })


@pytest.fixture
def trained_clf(clf_data: tuple[pd.DataFrame, pd.Series]) -> tuple[RandomForestClassifier, pd.DataFrame]:
    X, y = clf_data
    model = RandomForestClassifier(n_estimators=20, random_state=42)
    model.fit(X.values, y.values)
    return model, X


# ── Feature Engineering ───────────────────────────────────────────────────

class TestFeatureEngineering:
    def test_basic_pipeline(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result, meta = FeatureEngineeringEngine.build_pipeline(X, scaling_method="standard")
        assert result.shape[0] == X.shape[0]
        assert "final_shape" in meta

    def test_removes_duplicates(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        result, meta = FeatureEngineeringEngine.build_pipeline(df, remove_duplicates=True, scaling_method="none")
        assert meta["duplicates_removed"] == 1
        assert len(result) == 2

    def test_imputation_mean(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [4.0, 5.0, 6.0]})
        result, _ = FeatureEngineeringEngine.build_pipeline(df, imputation_strategy="mean", scaling_method="none")
        assert result["a"].isna().sum() == 0

    def test_onehot_encoding(self) -> None:
        df = pd.DataFrame({"num": [1.0, 2.0, 3.0], "cat": ["a", "b", "a"]})
        result, _ = FeatureEngineeringEngine.build_pipeline(df, encoding_method="onehot", scaling_method="none")
        assert "cat" not in result.columns
        assert result.shape[1] > 2

    def test_minmax_scaling(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, _ = clf_data
        result, _ = FeatureEngineeringEngine.build_pipeline(X, scaling_method="minmax")
        assert result.select_dtypes(include="number").values.min() >= -0.01
        assert result.select_dtypes(include="number").values.max() <= 1.01

    def test_polynomial_features(self) -> None:
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        result, meta = FeatureEngineeringEngine.build_pipeline(df, polynomial_degree=2, scaling_method="none")
        assert result.shape[1] > 2
        assert "polynomial_features" in meta

    def test_empty_dataframe_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureEngineeringEngine.build_pipeline(pd.DataFrame())

    def test_datetime_extraction(self) -> None:
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=5),
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })
        result, meta = FeatureEngineeringEngine.build_pipeline(df, extract_datetime=True, scaling_method="none")
        assert "date" not in result.columns
        assert any("year" in c or "month" in c for c in result.columns)


# ── Feature Selection ─────────────────────────────────────────────────────

class TestFeatureSelection:
    def test_variance_threshold(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, _ = clf_data
        result = FeatureSelector.variance_threshold(X, threshold=0.0)
        assert "selected_features" in result
        assert len(result["selected_features"]) > 0
        assert result["method"] == "variance_threshold"

    def test_select_k_best(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result = FeatureSelector.select_k_best(X, y, k=5)
        assert len(result["selected_features"]) == 5
        assert result["method"] == "select_k_best"

    def test_tree_importance(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result = FeatureSelector.tree_importance(X, y, threshold=0.0)
        assert len(result["selected_features"]) > 0
        assert all("score" in f for f in result["feature_ranking"])

    def test_mutual_information(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result = FeatureSelector.mutual_information(X, y, k=5)
        assert len(result["selected_features"]) == 5

    def test_rfe(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result = FeatureSelector.rfe(X, y, n_features=5)
        assert len(result["selected_features"]) == 5

    def test_correlation_based(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        result = FeatureSelector.correlation_based(X, y, threshold=0.99)
        assert "selected_features" in result

    def test_pca_reduction(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, _ = clf_data
        pca_df, meta = FeatureSelector.pca_reduction(X, n_components=5)
        assert pca_df.shape[1] == 5
        assert "explained_variance_ratio" in meta

    def test_unknown_method_raises(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        with pytest.raises(ValidationError):
            FeatureSelector.select(X, y, method="unknown_method")


# ── Algorithm Registry ────────────────────────────────────────────────────

class TestAlgorithmRegistry:
    def test_get_classification_estimator(self) -> None:
        model = get_estimator("classification", "random_forest")
        assert hasattr(model, "fit")

    def test_get_regression_estimator(self) -> None:
        model = get_estimator("regression", "ridge")
        assert hasattr(model, "fit")

    def test_get_clustering_estimator(self) -> None:
        model = get_estimator("clustering", "kmeans")
        assert hasattr(model, "fit")

    def test_unknown_algorithm_raises(self) -> None:
        with pytest.raises(ValidationError):
            get_estimator("classification", "unknown_algo")

    def test_unknown_model_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            get_estimator("unknown_type", "random_forest")

    def test_default_algorithms(self) -> None:
        algos = default_algorithms("classification")
        assert "random_forest" in algos
        assert "xgboost" in algos

    def test_hyperparameters_passed(self) -> None:
        model = get_estimator("classification", "random_forest", {"n_estimators": 50})
        assert model.n_estimators == 50


# ── Cross Validation ──────────────────────────────────────────────────────

class TestCrossValidation:
    def test_kfold(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        result = CrossValidator.run(model, X.values, y.values, strategy="kfold", n_splits=3)
        assert "strategy" in result
        assert result["strategy"] == "kfold"

    def test_stratified_kfold(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        result = CrossValidator.run(model, X.values, y.values, strategy="stratified_kfold", n_splits=3)
        assert result["n_splits"] == 3

    def test_timeseries_split(self, reg_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = reg_data
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        result = CrossValidator.run(model, X.values, y.values, model_type="regression", strategy="timeseries", n_splits=3)
        assert "strategy" in result

    def test_invalid_strategy_raises(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        with pytest.raises(ValidationError):
            CrossValidator.run(model, X.values, y.values, strategy="invalid")


# ── Model Evaluation ──────────────────────────────────────────────────────

class TestModelEvaluator:
    def test_classification_metrics(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        model = RandomForestClassifier(n_estimators=20, random_state=42)
        model.fit(X.values, y.values)
        y_pred = model.predict(X.values)
        y_prob = model.predict_proba(X.values)
        metrics = ModelEvaluator.classification_metrics(y.values, y_pred, y_prob)
        assert "accuracy" in metrics
        assert "f1_score" in metrics
        assert "roc_auc" in metrics
        assert "confusion_matrix" in metrics
        assert 0.0 <= metrics["accuracy"] <= 1.0

    def test_regression_metrics(self, reg_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = reg_data
        model = RandomForestRegressor(n_estimators=20, random_state=42)
        model.fit(X.values, y.values)
        y_pred = model.predict(X.values)
        metrics = ModelEvaluator.regression_metrics(y.values, y_pred)
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert metrics["mae"] >= 0

    def test_clustering_metrics(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        from sklearn.cluster import KMeans
        X, _ = clf_data
        model = KMeans(n_clusters=3, random_state=42, n_init=5)
        labels = model.fit_predict(X.values)
        metrics = ModelEvaluator.clustering_metrics(X.values, labels)
        assert "silhouette_score" in metrics
        assert "davies_bouldin_index" in metrics
        assert metrics["n_clusters"] == 3

    def test_compare_models(self) -> None:
        results = [
            {"algorithm": "rf", "metrics": {"f1_score": 0.85}},
            {"algorithm": "xgb", "metrics": {"f1_score": 0.90}},
            {"algorithm": "lr", "metrics": {"f1_score": 0.75}},
        ]
        comparison = ModelEvaluator.compare_models(results, "classification")
        assert comparison["best_model"] == "xgb"
        assert comparison["n_models"] == 3

    def test_compare_empty(self) -> None:
        result = ModelEvaluator.compare_models([], "classification")
        assert result["best_model"] is None


# ── Drift Detection ───────────────────────────────────────────────────────

class TestDriftDetector:
    def test_no_drift(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, _ = clf_data
        result = DriftDetector.detect_data_drift(X, X.copy())
        assert "drift_detected" in result
        assert result["drift_type"] == "data"

    def test_drift_detected(self) -> None:
        np.random.seed(42)
        ref = pd.DataFrame({"a": np.random.normal(0, 1, 200), "b": np.random.normal(5, 1, 200)})
        cur = pd.DataFrame({"a": np.random.normal(10, 1, 200), "b": np.random.normal(15, 1, 200)})
        result = DriftDetector.detect_data_drift(ref, cur)
        assert result["drift_detected"] is True
        assert result["drift_score"] > 0

    def test_prediction_drift(self) -> None:
        ref = np.random.normal(0.5, 0.1, 200)
        cur = np.random.normal(0.9, 0.1, 200)
        result = DriftDetector.detect_prediction_drift(ref, cur)
        assert "drift_type" in result
        assert result["drift_type"] == "prediction"

    def test_concept_drift(self) -> None:
        ref_metrics = {"accuracy": 0.90, "f1_score": 0.88}
        cur_metrics = {"accuracy": 0.75, "f1_score": 0.70}
        result = DriftDetector.detect_concept_drift(ref_metrics, cur_metrics)
        assert result["drift_detected"] is True
        assert "accuracy" in result["metric_degradations"]

    def test_no_concept_drift(self) -> None:
        ref_metrics = {"accuracy": 0.90}
        cur_metrics = {"accuracy": 0.89}
        result = DriftDetector.detect_concept_drift(ref_metrics, cur_metrics)
        assert result["drift_detected"] is False


# ── Model Monitoring ──────────────────────────────────────────────────────

class TestModelMonitor:
    def test_operational_metrics(self) -> None:
        from datetime import datetime, timezone
        records = [
            {"latency_ms": 50.0, "status": "success", "created_at": datetime.now(timezone.utc)},
            {"latency_ms": 120.0, "status": "success", "created_at": datetime.now(timezone.utc)},
            {"latency_ms": None, "status": "failed", "created_at": datetime.now(timezone.utc)},
        ]
        metrics = ModelMonitor.compute_operational_metrics(records)
        assert metrics["total_predictions"] == 3
        assert metrics["failed_predictions"] == 1
        assert metrics["failure_rate"] == pytest.approx(1 / 3, abs=0.01)
        assert "avg_latency_ms" in metrics

    def test_empty_records(self) -> None:
        result = ModelMonitor.compute_operational_metrics([])
        assert "error" in result

    def test_retraining_recommendation_critical(self) -> None:
        result = ModelMonitor.retraining_recommendation(
            drift_score=0.6, failure_rate=0.1, accuracy_degradation=0.15, days_since_training=100
        )
        assert result["recommend_retraining"] is True
        assert result["urgency"] == "critical"

    def test_retraining_recommendation_none(self) -> None:
        result = ModelMonitor.retraining_recommendation(
            drift_score=0.0, failure_rate=0.01, accuracy_degradation=0.0, days_since_training=10
        )
        assert result["recommend_retraining"] is False
        assert result["urgency"] == "none"


# ── Business AI Use Cases ─────────────────────────────────────────────────

class TestChurnPrediction:
    def test_predict(self, transaction_df: pd.DataFrame) -> None:
        result = ChurnPredictionService.predict(transaction_df)
        assert "total_customers" in result
        assert "churn_rate" in result
        assert 0.0 <= result["churn_rate"] <= 1.0
        assert "high_risk_customers" in result
        assert "customer_scores" in result

    def test_missing_columns(self) -> None:
        with pytest.raises(ValidationError):
            ChurnPredictionService.predict(pd.DataFrame({"a": [1, 2]}))


class TestCustomerSegmentation:
    def test_segment(self, transaction_df: pd.DataFrame) -> None:
        result = CustomerSegmentationService.segment(transaction_df, n_segments=3)
        assert result["n_segments"] == 3
        assert "segment_profiles" in result
        assert "customer_segments" in result
        assert len(result["segment_profiles"]) == 3

    def test_missing_columns(self) -> None:
        with pytest.raises(ValidationError):
            CustomerSegmentationService.segment(pd.DataFrame({"a": [1, 2]}))


class TestCLVPrediction:
    def test_predict(self, transaction_df: pd.DataFrame) -> None:
        result = CLVPredictionService.predict(transaction_df, prediction_months=6)
        assert result["total_customers"] > 0
        assert result["prediction_months"] == 6
        assert result["total_predicted_clv"] >= 0
        assert "top_clv_customers" in result

    def test_missing_columns(self) -> None:
        with pytest.raises(ValidationError):
            CLVPredictionService.predict(pd.DataFrame({"a": [1, 2]}))


class TestRevenueForecasting:
    def test_forecast(self, transaction_df: pd.DataFrame) -> None:
        result = RevenueForecastingService.forecast(transaction_df, periods=3)
        assert len(result["forecast"]) == 3
        assert result["total_forecast_revenue"] >= 0
        assert "trend" in result
        assert all("month" in f and "forecast" in f for f in result["forecast"])

    def test_insufficient_data_raises(self) -> None:
        df = pd.DataFrame({
            "order_date": pd.date_range("2023-01-01", periods=2, freq="ME"),
            "revenue": [100.0, 200.0],
        })
        with pytest.raises(ValidationError):
            RevenueForecastingService.forecast(df, periods=3)

    def test_missing_columns(self) -> None:
        with pytest.raises(ValidationError):
            RevenueForecastingService.forecast(pd.DataFrame({"a": [1, 2]}))


class TestSalesForecasting:
    def test_forecast(self, transaction_df: pd.DataFrame) -> None:
        result = SalesForecastingService.forecast(transaction_df, periods=3)
        assert "forecast" in result
        assert len(result["forecast"]) == 3


# ── Hyperparameter Optimization ───────────────────────────────────────────

class TestHyperparameterOptimizer:
    def test_random_search(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        from sklearn.ensemble import RandomForestClassifier as RFC
        model, meta = HyperparameterOptimizer.random_search(
            RFC(random_state=42), X.values, y.values,
            algorithm="random_forest", n_iter=3, cv=2,
        )
        assert hasattr(model, "predict")

    def test_grid_search(self, clf_data: tuple[pd.DataFrame, pd.Series]) -> None:
        X, y = clf_data
        from sklearn.linear_model import LogisticRegression
        model, meta = HyperparameterOptimizer.grid_search(
            LogisticRegression(max_iter=200, random_state=42),
            X.values, y.values,
            algorithm="logistic_regression",
            search_space={"C": [0.1, 1.0]},
            cv=2,
        )
        assert hasattr(model, "predict")
        assert "best_params" in meta
