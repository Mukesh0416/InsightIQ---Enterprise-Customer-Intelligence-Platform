"""
Enterprise AI Platform Service.

Orchestrates training, prediction, model registry, drift monitoring,
and explainability. Designed for async FastAPI with background task support.
"""

from __future__ import annotations

import io
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.drift.detector import DriftDetector
from app.ai.explainability.explainer import LIMEExplainer, SHAPExplainer
from app.ai.monitoring.monitor import ModelMonitor
from app.ai.pipelines.training_pipeline import TrainingPipeline
from app.ai.registry.artifact_store import load_artifact, save_artifact
from app.exceptions import NotFoundError, ValidationError
from app.models.ai import (
    DriftReport,
    FeatureMetadata,
    MLExperiment,
    MLModel,
    ModelArtifact,
    ModelMetrics,
    Prediction,
    PredictionBatch,
    TrainingRun,
)
from app.repositories.ai import (
    DriftReportRepository,
    MLExperimentRepository,
    MLModelRepository,
    ModelMetricsRepository,
    PredictionBatchRepository,
    PredictionRepository,
    TrainingRunRepository,
)
from app.repositories.dataset import DatasetRepository
from app.schemas.ai import BatchPredictRequest, PredictRequest, TrainRequest
from app.storage import get_storage_provider

logger = logging.getLogger(__name__)


class AIService:
    """
    Enterprise AI Platform Service.

    All heavy computation (training, batch prediction) is executed
    synchronously within background tasks so the async event loop
    is never blocked. The service layer persists results to the database.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.model_repo = MLModelRepository(session)
        self.experiment_repo = MLExperimentRepository(session)
        self.run_repo = TrainingRunRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.batch_repo = PredictionBatchRepository(session)
        self.metrics_repo = ModelMetricsRepository(session)
        self.drift_repo = DriftReportRepository(session)
        self.dataset_repo = DatasetRepository(session)
        self.storage = get_storage_provider()

    # ── Dataset helpers ───────────────────────────────────────────────────

    async def _load_raw(self, dataset_id: uuid.UUID) -> tuple[bytes, str]:
        """Load raw file bytes and extension for a dataset."""
        from app.models.dataset import Dataset
        dataset = await self.session.get(Dataset, dataset_id)
        if not dataset or dataset.is_deleted:
            raise NotFoundError(f"Dataset {dataset_id} not found.")
        version = await self.dataset_repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        file = await self.dataset_repo.get_file_by_version(version.id)
        if not file:
            raise NotFoundError("No stored file for current version.")
        data = await self.storage.read(file.storage_path)
        return data, file.file_extension

    # ── Training ──────────────────────────────────────────────────────────

    async def start_training(
        self,
        request: TrainRequest,
        organization_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Initiate a training experiment.

        Creates the experiment record and returns immediately.
        The actual training runs in a background task via run_training_job().
        """
        experiment = MLExperiment(
            name=request.experiment_name,
            dataset_id=request.dataset_id,
            organization_id=organization_id,
            owner_id=owner_id,
            model_type=request.model_type,
            target_column=request.target_column,
            feature_names=request.feature_columns,
            status="running",
            config=request.model_dump(exclude={"dataset_id"}),
        )
        self.session.add(experiment)
        await self.session.flush()
        await self.session.refresh(experiment)
        logger.info("Training experiment created: %s (%s)", experiment.id, request.experiment_name)
        return {
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "status": "running",
            "message": "Training started. Use GET /ai/experiments to track progress.",
        }

    async def run_training_job(
        self,
        experiment_id: uuid.UUID,
        request: TrainRequest,
        organization_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> None:
        """
        Execute the full training pipeline and persist results.

        Intended to be called from a background task.
        """
        logger.info("Training job started for experiment %s", experiment_id)
        try:
            raw_data, extension = await self._load_raw(request.dataset_id)
            pipeline = TrainingPipeline(request)

            # Run synchronously (CPU-bound; use thread pool in production)
            result = pipeline.run(raw_data, extension)

            best_model_id: uuid.UUID | None = None

            for run_data in result["run_results"]:
                # Persist TrainingRun
                run = TrainingRun(
                    experiment_id=experiment_id,
                    algorithm=run_data["algorithm"],
                    model_type=request.model_type,
                    status=run_data["status"],
                    hyperparameters=run_data.get("hyperparameters"),
                    metrics=run_data.get("metrics"),
                    cv_scores=run_data.get("cv_scores"),
                    feature_importance=run_data.get("feature_importance"),
                    training_duration_seconds=run_data.get("training_duration_seconds"),
                    error_message=run_data.get("error_message"),
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                self.session.add(run)
                await self.session.flush()
                await self.session.refresh(run)

                if run_data["status"] != "completed" or run_data.get("model_object") is None:
                    continue

                # Persist MLModel
                version = await self.model_repo.get_next_version(
                    f"{request.experiment_name}_{run_data['algorithm']}",
                    request.dataset_id,
                )
                model_record = MLModel(
                    name=f"{request.experiment_name}_{run_data['algorithm']}",
                    model_type=request.model_type,
                    algorithm=run_data["algorithm"],
                    version=version,
                    status="trained",
                    dataset_id=request.dataset_id,
                    organization_id=organization_id,
                    owner_id=owner_id,
                    feature_names=result["selected_features"],
                    target_column=request.target_column,
                    hyperparameters=run_data.get("hyperparameters"),
                    training_config=request.model_dump(exclude={"dataset_id"}),
                )
                self.session.add(model_record)
                await self.session.flush()
                await self.session.refresh(model_record)

                # Link run to model
                run.model_id = model_record.id
                await self.session.flush()

                # Save artifact
                artifact_meta = save_artifact(
                    run_data["model_object"],
                    str(model_record.id),
                    "model",
                    version,
                )
                model_record.artifact_path = artifact_meta["artifact_path"]

                artifact = ModelArtifact(
                    model_id=model_record.id,
                    artifact_type="model",
                    artifact_path=artifact_meta["artifact_path"],
                    file_size_bytes=artifact_meta["file_size_bytes"],
                    checksum_sha256=artifact_meta["checksum_sha256"],
                )
                self.session.add(artifact)

                # Persist metrics
                metrics_record = ModelMetrics(
                    model_id=model_record.id,
                    training_run_id=run.id,
                    metric_type="test",
                    metrics=run_data.get("metrics", {}),
                    confusion_matrix=run_data.get("metrics", {}).get("confusion_matrix"),
                    classification_report=run_data.get("metrics", {}).get("classification_report"),
                    feature_importance=run_data.get("feature_importance"),
                    evaluated_at=datetime.now(timezone.utc),
                )
                self.session.add(metrics_record)

                # Persist feature metadata
                for rank, feat_info in enumerate(result.get("feature_selection_result", {}).get("feature_ranking", [])[:50]):
                    fm = FeatureMetadata(
                        model_id=model_record.id,
                        feature_name=feat_info["feature"],
                        feature_type="numeric",
                        importance_score=feat_info.get("score") or feat_info.get("importance"),
                        importance_rank=rank + 1,
                        is_selected=feat_info["feature"] in result["selected_features"],
                        selection_method=result.get("feature_selection_result", {}).get("method"),
                    )
                    self.session.add(fm)

                if run_data["run_id"] == result.get("best_run_id"):
                    best_model_id = model_record.id

            await self.session.flush()

            # Mark experiment complete
            await self.experiment_repo.complete(experiment_id, best_model_id)
            await self.session.commit()
            logger.info("Training job completed for experiment %s. Best model: %s", experiment_id, best_model_id)

        except Exception as exc:
            await self.session.rollback()
            logger.error("Training job failed for experiment %s: %s", experiment_id, exc)
            exp = await self.session.get(MLExperiment, experiment_id)
            if exp:
                exp.status = "failed"
                await self.session.commit()

    # ── Prediction ────────────────────────────────────────────────────────

    async def predict(self, request: PredictRequest) -> dict[str, Any]:
        """Run a single prediction with optional SHAP explanation."""
        model_record = await self.session.get(MLModel, request.model_id)
        if not model_record or model_record.status == "archived":
            raise NotFoundError(f"Model {request.model_id} not found or archived.")
        if not model_record.artifact_path:
            raise ValidationError("Model artifact not available.")

        start = time.perf_counter()
        logger.info("Prediction request for model %s", request.model_id)

        try:
            model_obj = load_artifact(model_record.artifact_path)
            feature_names = model_record.feature_names or []
            input_df = pd.DataFrame([request.input_data])

            # Align columns
            for col in feature_names:
                if col not in input_df.columns:
                    input_df[col] = 0
            input_df = input_df[feature_names] if feature_names else input_df

            y_pred = model_obj.predict(input_df.values)
            predicted_label = str(y_pred[0]) if model_record.model_type == "classification" else None
            predicted_value = float(y_pred[0]) if model_record.model_type != "classification" else None

            prob_scores: dict[str, float] | None = None
            confidence: float | None = None
            if hasattr(model_obj, "predict_proba") and model_record.model_type == "classification":
                probs = model_obj.predict_proba(input_df.values)[0]
                classes = [str(c) for c in model_obj.classes_]
                prob_scores = {c: round(float(p), 4) for c, p in zip(classes, probs)}
                confidence = round(float(np.max(probs)), 4)

            explanation: dict[str, Any] | None = None
            if request.explain:
                try:
                    explanation = SHAPExplainer.local_explanation(model_obj, input_df, 0, feature_names)
                except Exception as exc:
                    logger.warning("SHAP explanation failed: %s", exc)

            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            pred_record = Prediction(
                model_id=request.model_id,
                input_data=request.input_data,
                predicted_label=predicted_label,
                predicted_value=predicted_value,
                confidence_score=confidence,
                probability_scores=prob_scores,
                explanation=explanation,
                latency_ms=latency_ms,
                status="success",
            )
            self.session.add(pred_record)
            await self.session.flush()
            await self.session.refresh(pred_record)
            await self.session.commit()

            logger.info("Prediction completed for model %s in %.1fms", request.model_id, latency_ms)
            return {
                "prediction_id": pred_record.id,
                "model_id": request.model_id,
                "predicted_label": predicted_label,
                "predicted_value": predicted_value,
                "confidence_score": confidence,
                "probability_scores": prob_scores,
                "explanation": explanation,
                "latency_ms": latency_ms,
                "created_at": pred_record.created_at,
            }

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            pred_record = Prediction(
                model_id=request.model_id,
                input_data=request.input_data,
                latency_ms=latency_ms,
                status="failed",
                error_message=str(exc),
            )
            self.session.add(pred_record)
            await self.session.commit()
            logger.error("Prediction failed for model %s: %s", request.model_id, exc)
            raise ValidationError(f"Prediction failed: {exc}") from exc

    async def start_batch_predict(self, request: BatchPredictRequest) -> dict[str, Any]:
        """Create a batch prediction job record."""
        model_record = await self.session.get(MLModel, request.model_id)
        if not model_record:
            raise NotFoundError(f"Model {request.model_id} not found.")

        batch = PredictionBatch(
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            status="pending",
        )
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        await self.session.commit()
        logger.info("Batch prediction job created: %s", batch.id)
        return {
            "batch_id": batch.id,
            "model_id": request.model_id,
            "status": "pending",
            "message": "Batch prediction queued.",
        }

    async def run_batch_predict_job(self, batch_id: uuid.UUID) -> None:
        """Execute batch prediction and persist results."""
        batch = await self.session.get(PredictionBatch, batch_id)
        if not batch:
            return

        batch.status = "running"
        batch.started_at = datetime.now(timezone.utc)
        await self.session.flush()

        try:
            model_record = await self.session.get(MLModel, batch.model_id)
            if not model_record or not model_record.artifact_path:
                raise ValidationError("Model artifact not available.")

            raw_data, extension = await self._load_raw(batch.dataset_id)
            df = pd.read_csv(io.BytesIO(raw_data)) if extension == ".csv" else pd.read_excel(io.BytesIO(raw_data))

            model_obj = load_artifact(model_record.artifact_path)
            feature_names = model_record.feature_names or []

            for col in feature_names:
                if col not in df.columns:
                    df[col] = 0
            X = df[feature_names].values if feature_names else df.select_dtypes(include="number").values

            batch.total_records = len(df)
            predictions = model_obj.predict(X)
            probs = model_obj.predict_proba(X) if hasattr(model_obj, "predict_proba") else None

            for i, pred_val in enumerate(predictions):
                prob_scores = None
                confidence = None
                if probs is not None:
                    classes = [str(c) for c in model_obj.classes_]
                    prob_scores = {c: round(float(p), 4) for c, p in zip(classes, probs[i])}
                    confidence = round(float(np.max(probs[i])), 4)

                pred_record = Prediction(
                    model_id=batch.model_id,
                    batch_id=batch_id,
                    input_data=df.iloc[i].to_dict(),
                    predicted_label=str(pred_val) if model_record.model_type == "classification" else None,
                    predicted_value=float(pred_val) if model_record.model_type != "classification" else None,
                    confidence_score=confidence,
                    probability_scores=prob_scores,
                    status="success",
                )
                self.session.add(pred_record)
                batch.processed_records += 1

            batch.status = "completed"
            batch.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.info("Batch prediction completed: %s (%d records)", batch_id, batch.processed_records)

        except Exception as exc:
            batch.status = "failed"
            batch.error_message = str(exc)
            batch.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.error("Batch prediction failed: %s — %s", batch_id, exc)

    # ── Model Registry ────────────────────────────────────────────────────

    async def list_models(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 50) -> list[MLModel]:
        return await self.model_repo.list_by_org(organization_id, skip=skip, limit=limit)

    async def get_model(self, model_id: uuid.UUID) -> MLModel:
        model = await self.session.get(MLModel, model_id)
        if not model:
            raise NotFoundError(f"Model {model_id} not found.")
        return model

    async def activate_model(self, model_id: uuid.UUID) -> None:
        await self.model_repo.activate(model_id)
        await self.session.commit()
        logger.info("Model activated: %s", model_id)

    async def archive_model(self, model_id: uuid.UUID) -> None:
        await self.model_repo.archive(model_id)
        await self.session.commit()
        logger.info("Model archived: %s", model_id)

    # ── Metrics ───────────────────────────────────────────────────────────

    async def get_metrics(self, model_id: uuid.UUID) -> list[ModelMetrics]:
        return await self.metrics_repo.get_by_model(model_id)

    # ── Explainability ────────────────────────────────────────────────────

    async def explain_prediction(self, prediction_id: uuid.UUID) -> dict[str, Any]:
        pred = await self.session.get(Prediction, prediction_id)
        if not pred:
            raise NotFoundError(f"Prediction {prediction_id} not found.")
        if pred.explanation:
            return pred.explanation

        model_record = await self.session.get(MLModel, pred.model_id)
        if not model_record or not model_record.artifact_path:
            raise ValidationError("Model artifact not available for explanation.")

        model_obj = load_artifact(model_record.artifact_path)
        feature_names = model_record.feature_names or []
        input_df = pd.DataFrame([pred.input_data or {}])
        for col in feature_names:
            if col not in input_df.columns:
                input_df[col] = 0
        input_df = input_df[feature_names] if feature_names else input_df

        try:
            explanation = SHAPExplainer.local_explanation(model_obj, input_df, 0, feature_names)
        except Exception:
            explanation = {"error": "SHAP explanation unavailable for this model type."}

        pred.explanation = explanation
        await self.session.commit()
        return explanation

    # ── Drift ─────────────────────────────────────────────────────────────

    async def run_drift_analysis(
        self,
        model_id: uuid.UUID,
        reference_dataset_id: uuid.UUID,
        current_dataset_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Run data drift analysis between reference and current datasets."""
        model_record = await self.session.get(MLModel, model_id)
        if not model_record:
            raise NotFoundError(f"Model {model_id} not found.")

        ref_raw, ref_ext = await self._load_raw(reference_dataset_id)
        cur_raw, cur_ext = await self._load_raw(current_dataset_id)

        ref_df = pd.read_csv(io.BytesIO(ref_raw)) if ref_ext == ".csv" else pd.read_excel(io.BytesIO(ref_raw))
        cur_df = pd.read_csv(io.BytesIO(cur_raw)) if cur_ext == ".csv" else pd.read_excel(io.BytesIO(cur_raw))

        feature_names = model_record.feature_names or []
        if feature_names:
            ref_df = ref_df[[c for c in feature_names if c in ref_df.columns]]
            cur_df = cur_df[[c for c in feature_names if c in cur_df.columns]]

        drift_result = DriftDetector.detect_data_drift(ref_df, cur_df)

        report = DriftReport(
            model_id=model_id,
            drift_type="data",
            drift_detected=drift_result["drift_detected"],
            drift_score=drift_result["drift_score"],
            feature_drift=drift_result["feature_drift"],
            statistical_tests={"ks_tests": {k: v.get("ks_test") for k, v in drift_result["feature_drift"].items() if "ks_test" in v}},
            recommendations=drift_result["recommendations"],
        )
        self.session.add(report)
        await self.session.commit()

        if drift_result["drift_detected"]:
            logger.warning("Drift detected for model %s: score=%.4f", model_id, drift_result["drift_score"])

        return drift_result

    async def get_drift_reports(self, model_id: uuid.UUID) -> list[DriftReport]:
        return await self.drift_repo.list_by_model(model_id)

    # ── Experiments ───────────────────────────────────────────────────────

    async def list_experiments(self, organization_id: uuid.UUID, skip: int = 0, limit: int = 50) -> list[MLExperiment]:
        return await self.experiment_repo.list_by_org(organization_id, skip=skip, limit=limit)

    async def get_training_history(self, model_id: uuid.UUID) -> list[TrainingRun]:
        return await self.run_repo.list_by_model(model_id)

    # ── Monitoring ────────────────────────────────────────────────────────

    async def get_model_monitoring(self, model_id: uuid.UUID) -> dict[str, Any]:
        """Compute operational monitoring metrics for a model."""
        predictions = await self.prediction_repo.list_by_model(model_id, limit=1000)
        records = [
            {
                "latency_ms": p.latency_ms,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in predictions
        ]
        ops_metrics = ModelMonitor.compute_operational_metrics(records)

        # Drift summary
        latest_drift = await self.drift_repo.latest(model_id)
        drift_summary = {
            "drift_detected": latest_drift.drift_detected if latest_drift else False,
            "drift_score": latest_drift.drift_score if latest_drift else None,
            "last_checked": latest_drift.created_at.isoformat() if latest_drift else None,
        }

        # Retraining recommendation
        model_record = await self.session.get(MLModel, model_id)
        days_since = 0
        if model_record and model_record.created_at:
            days_since = (datetime.now(timezone.utc) - model_record.created_at).days

        retraining = ModelMonitor.retraining_recommendation(
            drift_score=latest_drift.drift_score or 0.0 if latest_drift else 0.0,
            failure_rate=ops_metrics.get("failure_rate", 0.0),
            accuracy_degradation=0.0,
            days_since_training=days_since,
        )

        return {
            "model_id": str(model_id),
            "operational_metrics": ops_metrics,
            "drift_summary": drift_summary,
            "retraining_recommendation": retraining,
        }
