"""
Repository layer for the Enterprise AI Platform.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import (
    DriftReport,
    MLExperiment,
    MLModel,
    ModelMetrics,
    Prediction,
    PredictionBatch,
    TrainingRun,
)


class MLModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MLModel]:
        stmt = (
            select(MLModel)
            .where(MLModel.organization_id == organization_id)
            .order_by(MLModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_version(self, name: str, dataset_id: UUID) -> int:
        stmt = (
            select(func.max(MLModel.version))
            .where(MLModel.name == name, MLModel.dataset_id == dataset_id)
        )
        max_version = (await self.session.execute(stmt)).scalar_one_or_none()
        return (max_version or 0) + 1

    async def activate(self, model_id: UUID) -> None:
        from datetime import datetime, timezone
        await self.session.execute(
            update(MLModel)
            .where(MLModel.id == model_id)
            .values(status="active", is_champion=True, activated_at=datetime.now(timezone.utc))
        )

    async def archive(self, model_id: UUID) -> None:
        from datetime import datetime, timezone
        await self.session.execute(
            update(MLModel)
            .where(MLModel.id == model_id)
            .values(status="archived", is_champion=False, archived_at=datetime.now(timezone.utc))
        )


class MLExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MLExperiment]:
        stmt = (
            select(MLExperiment)
            .where(MLExperiment.organization_id == organization_id)
            .order_by(MLExperiment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def complete(self, experiment_id: UUID, best_model_id: UUID | None = None) -> None:
        from datetime import datetime, timezone
        values: dict[str, Any] = {"status": "completed", "completed_at": datetime.now(timezone.utc)}
        if best_model_id:
            values["best_model_id"] = best_model_id
        await self.session.execute(
            update(MLExperiment).where(MLExperiment.id == experiment_id).values(**values)
        )


class TrainingRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_model(self, model_id: UUID) -> list[TrainingRun]:
        stmt = (
            select(TrainingRun)
            .where(TrainingRun.model_id == model_id)
            .order_by(TrainingRun.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_model(self, model_id: UUID, limit: int = 1000) -> list[Prediction]:
        stmt = (
            select(Prediction)
            .where(Prediction.model_id == model_id)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PredictionBatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class ModelMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_model(self, model_id: UUID) -> list[ModelMetrics]:
        stmt = (
            select(ModelMetrics)
            .where(ModelMetrics.model_id == model_id)
            .order_by(ModelMetrics.evaluated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class DriftReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_model(self, model_id: UUID) -> list[DriftReport]:
        stmt = (
            select(DriftReport)
            .where(DriftReport.model_id == model_id)
            .order_by(DriftReport.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def latest(self, model_id: UUID) -> DriftReport | None:
        stmt = (
            select(DriftReport)
            .where(DriftReport.model_id == model_id)
            .order_by(DriftReport.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()