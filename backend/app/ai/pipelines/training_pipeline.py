"""Training pipeline for ML models."""

from __future__ import annotations

import io
import time
from typing import Any

import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.schemas.ai import TrainRequest


class TrainingPipeline:
    """Runs ML training for classification, regression, and clustering."""

    def __init__(self, request: TrainRequest) -> None:
        self.request = request

    def run(self, raw_data: bytes, extension: str) -> dict[str, Any]:
        """Execute the training pipeline synchronously."""
        start = time.perf_counter()

        if extension == ".csv":
            df = pd.read_csv(io.BytesIO(raw_data))
        else:
            df = pd.read_excel(io.BytesIO(raw_data))

        # Separate features and target
        if self.request.model_type in ("classification", "regression") and self.request.target_column:
            if self.request.target_column not in df.columns:
                raise ValueError(f"Target column '{self.request.target_column}' not found in dataset")
            y = df[self.request.target_column]
            X = df.drop(columns=[self.request.target_column])
        else:
            X = df.select_dtypes(include=["number"])
            y = None

        # Handle feature selection
        feature_cols = [str(c) for c in X.columns]
        if self.request.feature_columns:
            feature_cols = [c for c in self.request.feature_columns if c in X.columns]
            X = X[feature_cols]

        # Encode categorical features
        for col in X.select_dtypes(include=["object"]).columns:
            X[col] = X[col].astype("category").cat.codes

        # Fill missing values
        X = X.fillna(X.mean(numeric_only=True) if X.select_dtypes(include=["number"]).shape[1] > 0 else 0)

        # Select algorithms based on model type
        algorithms = self.request.algorithms or self._default_algorithms()
        run_results = []
        best_run_id = None
        best_score = -float("inf")

        for algo in algorithms[:3]:  # Limit to 3 algorithms for speed
            run_start = time.perf_counter()
            run_data: dict[str, Any] = {
                "algorithm": algo,
                "model_type": self.request.model_type,
                "status": "completed",
                "hyperparameters": {"algorithm": algo},
                "started_at": pd.Timestamp.utcnow().isoformat(),
                "completed_at": pd.Timestamp.utcnow().isoformat(),
                "training_duration_seconds": 0.0,
            }

            try:
                model = self._get_model(algo)
                if model is None:
                    run_data["status"] = "failed"
                    run_data["error_message"] = f"Unsupported algorithm: {algo}"
                    run_results.append(run_data)
                    continue

                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X.values)

                if y is not None:
                    y_series = pd.to_numeric(y, errors="coerce") if self.request.model_type == "regression" else y.astype(str)
                    # Train/test split
                    from sklearn.model_selection import train_test_split

                    X_train, X_test, y_train, y_test = train_test_split(
                        X_scaled, y_series, test_size=self.request.test_size, random_state=self.request.random_state
                    )
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)

                    # Compute metrics
                    metrics = self._compute_metrics(y_test, y_pred, self.request.model_type)
                    run_data["metrics"] = metrics

                    # Feature importance
                    if hasattr(model, "feature_importances_"):
                        imp = model.feature_importances_
                        run_data["feature_importance"] = {
                            str(f): round(float(v), 4) for f, v in zip(feature_cols, imp)
                        }

                    score = metrics.get("accuracy", metrics.get("r2", 0.0)) or 0.0
                    run_data["score"] = score
                    run_data["model_object"] = model

                    if score > best_score:
                        best_score = score
                        best_run_id = run_data.get("run_id", str(len(run_results)))
                else:
                    # Unsupervised clustering
                    model.fit(X_scaled)
                    from sklearn.metrics import silhouette_score

                    labels = model.labels_
                    try:
                        sil = float(silhouette_score(X_scaled, labels))
                        run_data["metrics"] = {"silhouette_score": round(sil, 4)}
                        run_data["score"] = sil
                    except Exception:
                        run_data["metrics"] = {"silhouette_score": 0.0}
                        run_data["score"] = 0.0
                    run_data["model_object"] = model

                run_data["training_duration_seconds"] = round(time.perf_counter() - run_start, 3)
            except Exception as exc:
                run_data["status"] = "failed"
                run_data["error_message"] = str(exc)

            run_results.append(run_data)

        return {
            "run_results": run_results,
            "best_run_id": best_run_id,
            "selected_features": feature_cols,
            "feature_selection_result": {"method": "all", "feature_ranking": []},
            "processing_time_ms": round((time.perf_counter() - start) * 1000, 2),
        }

    def _default_algorithms(self) -> list[str]:
        if self.request.model_type == "classification":
            return ["random_forest", "logistic_regression", "gradient_boosting"]
        if self.request.model_type == "regression":
            return ["random_forest_regressor", "linear_regression", "gradient_boosting_regressor"]
        return ["kmeans", "dbscan", "hierarchical"]

    def _get_model(self, algorithm: str) -> Any:
        if algorithm in ("random_forest", "random_forest_classifier"):
            return RandomForestClassifier(n_estimators=100, random_state=self.request.random_state)
        if algorithm == "logistic_regression":
            return LogisticRegression(max_iter=1000, random_state=self.request.random_state)
        if algorithm == "gradient_boosting":
            return GradientBoostingClassifier(n_estimators=100, random_state=self.request.random_state)
        if algorithm in ("random_forest_regressor",):
            return RandomForestRegressor(n_estimators=100, random_state=self.request.random_state)
        if algorithm == "linear_regression":
            return LinearRegression()
        if algorithm == "gradient_boosting_regressor":
            return GradientBoostingRegressor(n_estimators=100, random_state=self.request.random_state)
        if algorithm == "kmeans":
            from sklearn.cluster import KMeans
            return KMeans(n_clusters=5, random_state=self.request.random_state, n_init=10)
        if algorithm == "dbscan":
            from sklearn.cluster import DBSCAN
            return DBSCAN()
        if algorithm == "hierarchical":
            from sklearn.cluster import AgglomerativeClustering
            return AgglomerativeClustering(n_clusters=5)
        return None

    @staticmethod
    def _compute_metrics(y_true: pd.Series, y_pred: Any, model_type: str) -> dict[str, Any]:
        from sklearn.metrics import (
            accuracy_score,
            confusion_matrix,
            f1_score,
            mean_absolute_error,
            mean_squared_error,
            precision_score,
            r2_score,
            recall_score,
        )

        metrics: dict[str, Any] = {}
        if model_type == "classification":
            metrics["accuracy"] = round(float(accuracy_score(y_true, y_pred)), 4)
            metrics["precision"] = round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4)
            metrics["recall"] = round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4)
            metrics["f1_score"] = round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4)
            metrics["confusion_matrix"] = confusion_matrix(y_true, y_pred).tolist()
        else:
            metrics["rmse"] = round(float(mean_squared_error(y_true, y_pred, squared=False)), 4)
            metrics["mae"] = round(float(mean_absolute_error(y_true, y_pred)), 4)
            metrics["r2"] = round(float(r2_score(y_true, y_pred)), 4)
        return metrics