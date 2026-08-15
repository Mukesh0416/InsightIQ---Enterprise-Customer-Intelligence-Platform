"""
Pydantic v2 schemas for the Enterprise AI Platform.

Covers training requests, prediction requests, model responses,
metrics, drift reports, and experiment schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enums / Literals ──────────────────────────────────────────────────────

CLASSIFICATION_ALGORITHMS = [
    "logistic_regression", "decision_tree", "random_forest", "extra_trees",
    "xgboost", "lightgbm", "catboost", "gradient_boosting", "adaboost",
    "naive_bayes", "svm", "knn",
]

REGRESSION_ALGORITHMS = [
    "linear_regression", "ridge", "lasso", "elasticnet",
    "random_forest_regressor", "xgboost_regressor",
    "catboost_regressor", "lightgbm_regressor",
]

CLUSTERING_ALGORITHMS = ["kmeans", "dbscan", "agglomerative"]

ALL_ALGORITHMS = CLASSIFICATION_ALGORITHMS + REGRESSION_ALGORITHMS + CLUSTERING_ALGORITHMS


# ── Training ──────────────────────────────────────────────────────────────

class FeatureEngineeringConfig(BaseModel):
    imputation_strategy: str = "mean"
    remove_duplicates: bool = True
    outlier_method: str | None = "iqr"
    encoding_method: str = "onehot"
    scaling_method: str = "standard"
    normalize: bool = False
    extract_datetime: bool = True
    polynomial_degree: int | None = None
    interaction_features: bool = False
    binning_columns: list[str] = Field(default_factory=list)
    text_columns: list[str] = Field(default_factory=list)


class FeatureSelectionConfig(BaseModel):
    method: str = "tree_importance"
    k_best: int | None = None
    variance_threshold: float = 0.0
    correlation_threshold: float = 0.95
    use_pca: bool = False
    pca_components: int | None = None


class HyperparameterOptConfig(BaseModel):
    method: str = "optuna"
    n_trials: int = 50
    cv_folds: int = 5
    cv_strategy: str = "stratified_kfold"
    search_space: dict[str, Any] | None = None
    timeout_seconds: int | None = 300


class TrainRequest(BaseModel):
    dataset_id: UUID
    experiment_name: str = Field(min_length=1, max_length=256)
    model_type: str = Field(pattern="^(classification|regression|clustering)$")
    target_column: str | None = None
    feature_columns: list[str] | None = None
    algorithms: list[str] | None = None
    feature_engineering: FeatureEngineeringConfig = Field(default_factory=FeatureEngineeringConfig)
    feature_selection: FeatureSelectionConfig = Field(default_factory=FeatureSelectionConfig)
    hyperparameter_opt: HyperparameterOptConfig = Field(default_factory=HyperparameterOptConfig)
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)
    random_state: int = 42

    @field_validator("algorithms")
    @classmethod
    def validate_algorithms(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            invalid = [a for a in v if a not in ALL_ALGORITHMS]
            if invalid:
                raise ValueError(f"Unknown algorithms: {invalid}")
        return v

    @model_validator(mode="after")
    def validate_target_for_supervised(self) -> TrainRequest:
        if self.model_type in ("classification", "regression") and not self.target_column:
            raise ValueError("target_column is required for supervised learning")
        return self


# ── Prediction ────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    model_id: UUID
    input_data: dict[str, Any]
    explain: bool = False


class BatchPredictRequest(BaseModel):
    model_id: UUID
    dataset_id: UUID
    explain: bool = False


# ── Responses ─────────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    prediction_id: UUID
    model_id: UUID
    predicted_label: str | None
    predicted_value: float | None
    confidence_score: float | None
    probability_scores: dict[str, float] | None
    explanation: dict[str, Any] | None
    latency_ms: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_type: str
    algorithm: str
    version: int
    status: str
    is_champion: bool
    feature_names: list[str] | None
    target_column: str | None
    hyperparameters: dict[str, Any] | None
    mlflow_run_id: str | None
    created_at: datetime
    activated_at: datetime | None
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class MetricsResponse(BaseModel):
    model_id: UUID
    metric_type: str
    metrics: dict[str, Any]
    confusion_matrix: list | None
    classification_report: dict | None
    feature_importance: dict[str, float] | None
    evaluated_at: datetime | None

    model_config = {"from_attributes": True}


class DriftReportResponse(BaseModel):
    id: UUID
    model_id: UUID
    drift_type: str
    drift_detected: bool
    drift_score: float | None
    feature_drift: dict[str, Any] | None
    prediction_drift: dict[str, Any] | None
    statistical_tests: dict[str, Any] | None
    recommendations: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    model_type: str
    status: str
    best_model_id: UUID | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TrainingRunResponse(BaseModel):
    id: UUID
    algorithm: str
    model_type: str
    status: str
    hyperparameters: dict[str, Any] | None
    metrics: dict[str, Any] | None
    cv_scores: dict[str, Any] | None
    training_duration_seconds: float | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TrainResponse(BaseModel):
    experiment_id: UUID
    experiment_name: str
    status: str
    message: str


class BatchPredictResponse(BaseModel):
    batch_id: UUID
    model_id: UUID
    status: str
    message: str
