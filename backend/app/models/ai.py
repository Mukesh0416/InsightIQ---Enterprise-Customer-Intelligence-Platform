"""
SQLAlchemy ORM models for the Enterprise AI Platform.

Covers MLModel, MLExperiment, TrainingRun, Prediction, PredictionBatch,
ModelMetrics, DriftReport, FeatureMetadata, and ModelArtifact.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.types import UUID
from app.models.base import BaseModel


class MLModel(BaseModel):
    """Registered ML model with versioning and lifecycle management."""

    __tablename__ = "ml_models"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
        comment="classification | regression | clustering",
    )
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="trained", index=True,
        comment="trained | active | archived | failed",
    )
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    feature_names: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_column: Mapped[str | None] = mapped_column(String(256), nullable=True)
    hyperparameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    training_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mlflow_model_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    training_runs: Mapped[list[TrainingRun]] = relationship(
        "TrainingRun", back_populates="model", cascade="all, delete-orphan", lazy="selectin",
    )
    metrics: Mapped[list[ModelMetrics]] = relationship(
        "ModelMetrics", back_populates="model", cascade="all, delete-orphan", lazy="selectin",
    )
    artifacts: Mapped[list[ModelArtifact]] = relationship(
        "ModelArtifact", back_populates="model", cascade="all, delete-orphan", lazy="selectin",
    )
    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="model", cascade="all, delete-orphan", lazy="noload",
    )
    drift_reports: Mapped[list[DriftReport]] = relationship(
        "DriftReport", back_populates="model", cascade="all, delete-orphan", lazy="noload",
    )


class MLExperiment(BaseModel):
    """ML experiment grouping multiple training runs."""

    __tablename__ = "ml_experiments"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    model_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_column: Mapped[str | None] = mapped_column(String(256), nullable=True)
    feature_names: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="running", index=True,
        comment="running | completed | failed",
    )
    best_model_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)
    mlflow_experiment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    training_runs: Mapped[list[TrainingRun]] = relationship(
        "TrainingRun", back_populates="experiment", cascade="all, delete-orphan", lazy="selectin",
    )


class TrainingRun(BaseModel):
    """Individual training run within an experiment."""

    __tablename__ = "training_runs"

    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("ml_experiments.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    model_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="pending | running | completed | failed",
    )
    hyperparameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cv_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feature_importance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    training_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    experiment: Mapped[MLExperiment | None] = relationship("MLExperiment", back_populates="training_runs")
    model: Mapped[MLModel | None] = relationship("MLModel", back_populates="training_runs")


class Prediction(BaseModel):
    """Single prediction record with metadata and explanation."""

    __tablename__ = "predictions"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("prediction_batches.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prediction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    predicted_label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    predicted_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="success",
        comment="success | failed",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="predictions")
    batch: Mapped[PredictionBatch | None] = relationship("PredictionBatch", back_populates="predictions")


class PredictionBatch(BaseModel):
    """Batch prediction job tracking."""

    __tablename__ = "prediction_batches"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="pending | running | completed | failed",
    )
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="batch", cascade="all, delete-orphan", lazy="noload",
    )


class ModelMetrics(BaseModel):
    """Evaluation metrics snapshot for a model."""

    __tablename__ = "model_metrics"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    training_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("training_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    metric_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="train | validation | test | production",
    )
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confusion_matrix: Mapped[list | None] = mapped_column(JSON, nullable=True)
    classification_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feature_importance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="metrics")


class DriftReport(BaseModel):
    """Data and concept drift monitoring report."""

    __tablename__ = "drift_reports"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    drift_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="data | concept | prediction | feature",
    )
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    drift_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_drift: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prediction_drift: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    statistical_tests: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    reference_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="drift_reports")


class FeatureMetadata(BaseModel):
    """Feature engineering metadata and statistics."""

    __tablename__ = "feature_metadata"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    feature_name: Mapped[str] = mapped_column(String(256), nullable=False)
    feature_type: Mapped[str] = mapped_column(String(32), nullable=False)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    statistics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    selection_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transformation: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ModelArtifact(BaseModel):
    """Stored model artifact (serialized model, preprocessor, etc.)."""

    __tablename__ = "model_artifacts"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="model | preprocessor | feature_selector | encoder | scaler",
    )
    artifact_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    model: Mapped[MLModel] = relationship("MLModel", back_populates="artifacts")
