"""
Enterprise AI Platform API Endpoints.

POST /ai/train
POST /ai/predict
POST /ai/predict/batch
GET  /ai/models
GET  /ai/models/{id}
POST /ai/models/{id}/activate
POST /ai/models/{id}/archive
GET  /ai/metrics/{model_id}
GET  /ai/explain/{prediction_id}
GET  /ai/drift/{model_id}
GET  /ai/experiments
GET  /ai/training-history
GET  /ai/monitoring/{model_id}
GET  /ai/business/churn/{dataset_id}
GET  /ai/business/segmentation/{dataset_id}
GET  /ai/business/clv/{dataset_id}
GET  /ai/business/revenue-forecast/{dataset_id}
GET  /ai/business/sales-forecast/{dataset_id}
"""

from __future__ import annotations

import io
import logging
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.ai import (
    BatchPredictRequest,
    BatchPredictResponse,
    DriftReportResponse,
    ExperimentResponse,
    MetricsResponse,
    ModelResponse,
    PredictRequest,
    PredictionResponse,
    TrainRequest,
    TrainResponse,
    TrainingRunResponse,
)
from app.services.ai import AIService
from app.services.business_ai import (
    ChurnPredictionService,
    CLVPredictionService,
    CustomerSegmentationService,
    ProductRecommendationService,
    RevenueForecastingService,
    SalesForecastingService,
)
from app.storage import get_storage_provider
from app.repositories.dataset import DatasetRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Enterprise AI Platform"])


def _get_service(session: AsyncSession) -> AIService:
    return AIService(session)


# ── Training ──────────────────────────────────────────────────────────────

@router.post("/train", response_model=TrainResponse, status_code=202)
async def train_model(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.train")),
) -> TrainResponse:
    """
    Start an ML training experiment.

    Supports classification, regression, and clustering with
    automatic feature engineering, selection, and hyperparameter optimization.
    Training runs asynchronously in the background.
    """
    service = _get_service(session)
    result = await service.start_training(request)
    background_tasks.add_task(
        service.run_training_job,
        result["experiment_id"],
        request,
    )
    return TrainResponse(**result)


# ── Prediction ────────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> PredictionResponse:
    """Run a single prediction with optional SHAP explanation."""
    service = _get_service(session)
    result = await service.predict(request)
    return PredictionResponse(**result)


@router.post("/predict/batch", response_model=BatchPredictResponse, status_code=202)
async def batch_predict(
    request: BatchPredictRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> BatchPredictResponse:
    """Queue a batch prediction job over a full dataset."""
    service = _get_service(session)
    result = await service.start_batch_predict(request)
    background_tasks.add_task(service.run_batch_predict_job, result["batch_id"])
    return BatchPredictResponse(**result)


# ── Model Registry ────────────────────────────────────────────────────────

@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    organization_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> list[ModelResponse]:
    """List all registered models for an organization."""
    service = _get_service(session)
    models = await service.list_models(organization_id, skip=skip, limit=limit)
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> ModelResponse:
    """Get a specific model by ID."""
    service = _get_service(session)
    model = await service.get_model(model_id)
    return ModelResponse.model_validate(model)


@router.post("/models/{model_id}/activate", status_code=204, response_class=Response)
async def activate_model(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.manage")),
) -> Response:
    """Activate a model as the champion for its type and dataset."""
    service = _get_service(session)
    await service.activate_model(model_id)
    logger.info("Model activated via API: %s", model_id)
    return Response(status_code=204)


@router.post("/models/{model_id}/archive", status_code=204, response_class=Response)
async def archive_model(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.manage")),
) -> Response:
    """Archive a model, removing it from active use."""
    service = _get_service(session)
    await service.archive_model(model_id)
    logger.info("Model archived via API: %s", model_id)
    return Response(status_code=204)


# ── Metrics ───────────────────────────────────────────────────────────────

@router.get("/metrics/{model_id}", response_model=list[MetricsResponse])
async def get_metrics(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> list[MetricsResponse]:
    """Get all evaluation metrics for a model."""
    service = _get_service(session)
    metrics = await service.get_metrics(model_id)
    return [MetricsResponse.model_validate(m) for m in metrics]


# ── Explainability ────────────────────────────────────────────────────────

@router.get("/explain/{prediction_id}")
async def explain_prediction(
    prediction_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> dict:
    """Get SHAP explanation for a specific prediction."""
    service = _get_service(session)
    return await service.explain_prediction(prediction_id)


# ── Drift ─────────────────────────────────────────────────────────────────

@router.get("/drift/{model_id}", response_model=list[DriftReportResponse])
async def get_drift_reports(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> list[DriftReportResponse]:
    """Get drift monitoring reports for a model."""
    service = _get_service(session)
    reports = await service.get_drift_reports(model_id)
    return [DriftReportResponse.model_validate(r) for r in reports]


@router.post("/drift/{model_id}/analyze", status_code=202)
async def run_drift_analysis(
    model_id: UUID,
    reference_dataset_id: UUID = Query(...),
    current_dataset_id: UUID = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.manage")),
) -> dict:
    """Trigger drift analysis between reference and current datasets."""
    service = _get_service(session)
    result = await service.run_drift_analysis(model_id, reference_dataset_id, current_dataset_id)
    return result


# ── Experiments & History ─────────────────────────────────────────────────

@router.get("/experiments", response_model=list[ExperimentResponse])
async def list_experiments(
    organization_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> list[ExperimentResponse]:
    """List all ML experiments for an organization."""
    service = _get_service(session)
    experiments = await service.list_experiments(organization_id, skip=skip, limit=limit)
    return [ExperimentResponse.model_validate(e) for e in experiments]


@router.get("/training-history", response_model=list[TrainingRunResponse])
async def get_training_history(
    model_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> list[TrainingRunResponse]:
    """Get training run history for a model."""
    service = _get_service(session)
    runs = await service.get_training_history(model_id)
    return [TrainingRunResponse.model_validate(r) for r in runs]


# ── Monitoring ────────────────────────────────────────────────────────────

@router.get("/monitoring/{model_id}")
async def get_model_monitoring(
    model_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.view")),
) -> dict:
    """Get operational monitoring metrics, drift summary, and retraining recommendations."""
    service = _get_service(session)
    return await service.get_model_monitoring(model_id)


# ── Business AI Use Cases ─────────────────────────────────────────────────

async def _load_df(dataset_id: UUID, session: AsyncSession) -> pd.DataFrame:
    """Load a dataset into a DataFrame."""
    from app.models.dataset import Dataset
    storage = get_storage_provider()
    repo = DatasetRepository(session)
    dataset = await session.get(Dataset, dataset_id)
    if not dataset or dataset.is_deleted:
        from app.exceptions import NotFoundError
        raise NotFoundError(f"Dataset {dataset_id} not found.")
    version = await repo.get_current_version(dataset_id)
    if not version:
        from app.exceptions import NotFoundError
        raise NotFoundError("Dataset has no current version.")
    file = await repo.get_file_by_version(version.id)
    if not file:
        from app.exceptions import NotFoundError
        raise NotFoundError("No stored file for current version.")
    data = await storage.read(file.storage_path)
    return pd.read_csv(io.BytesIO(data)) if file.file_extension == ".csv" else pd.read_excel(io.BytesIO(data))


@router.get("/business/churn/{dataset_id}")
async def churn_prediction(
    dataset_id: UUID,
    churn_days: int = Query(90, ge=7, le=365),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Predict customer churn probability using RFM + gradient boosting."""
    df = await _load_df(dataset_id, session)
    return ChurnPredictionService.predict(df, churn_days=churn_days)


@router.get("/business/segmentation/{dataset_id}")
async def customer_segmentation(
    dataset_id: UUID,
    n_segments: int = Query(5, ge=2, le=10),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Segment customers using KMeans on RFM features."""
    df = await _load_df(dataset_id, session)
    return CustomerSegmentationService.segment(df, n_segments=n_segments)


@router.get("/business/clv/{dataset_id}")
async def clv_prediction(
    dataset_id: UUID,
    prediction_months: int = Query(12, ge=1, le=60),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Predict Customer Lifetime Value using RFM + Ridge regression."""
    df = await _load_df(dataset_id, session)
    return CLVPredictionService.predict(df, prediction_months=prediction_months)


@router.get("/business/revenue-forecast/{dataset_id}")
async def revenue_forecast(
    dataset_id: UUID,
    periods: int = Query(6, ge=1, le=24),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Forecast monthly revenue for the next N periods."""
    df = await _load_df(dataset_id, session)
    return RevenueForecastingService.forecast(df, periods=periods)


@router.get("/business/sales-forecast/{dataset_id}")
async def sales_forecast(
    dataset_id: UUID,
    periods: int = Query(6, ge=1, le=24),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Forecast monthly sales volume for the next N periods."""
    df = await _load_df(dataset_id, session)
    return SalesForecastingService.forecast(df, periods=periods)


@router.get("/business/recommendations/{dataset_id}")
async def product_recommendations(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("ai.predict")),
) -> dict:
    """Get product recommendation architecture and top products."""
    df = await _load_df(dataset_id, session)
    return {
        "architecture": ProductRecommendationService.get_architecture(),
        "top_products": ProductRecommendationService.top_products_per_segment(df),
    }
