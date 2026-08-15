"""
Background Job Engine.

Provides a job queue abstraction with retry strategy, progress tracking,
job history, cancellation, and structured logging.
Designed so Celery/Redis Queue can be plugged in without changing business logic.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.services import BackgroundJob
from app.repositories.services import BackgroundJobRepository

logger = logging.getLogger(__name__)


class JobEngine:
    """
    In-process async job engine.

    For production scale, replace _execute_job with a Celery task dispatch.
    The BackgroundJob record is always persisted regardless of executor.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = BackgroundJobRepository(session)

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        *,
        organization_id: UUID | None = None,
        owner_id: UUID | None = None,
        priority: int = 5,
        max_retries: int = 3,
    ) -> BackgroundJob:
        """
        Create a job record and return it.

        The caller is responsible for dispatching execution via
        run_job() or a background task.
        """
        job = BackgroundJob(
            job_type=job_type,
            status="pending",
            priority=priority,
            organization_id=organization_id,
            owner_id=owner_id,
            payload=payload,
            max_retries=max_retries,
            logs=[],
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        logger.info("Job enqueued: %s (id=%s)", job_type, job.id)
        return job

    async def run_job(
        self,
        job_id: UUID,
        handler: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    ) -> None:
        """
        Execute a job handler with retry logic.

        Args:
            job_id: The BackgroundJob primary key.
            handler: Async callable that accepts (job_id, payload) and returns a result dict.
        """
        job = await self.session.get(BackgroundJob, job_id)
        if not job or job.status == "cancelled":
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self._append_log(job, f"Job started: {job.job_type}")

        for attempt in range(job.max_retries + 1):
            try:
                result = await handler(job_id, job.payload or {})
                job.status = "completed"
                job.result = result
                job.progress = 100.0
                job.completed_at = datetime.now(timezone.utc)
                await self._append_log(job, "Job completed successfully.")
                await self.session.commit()
                logger.info("Job completed: %s (id=%s)", job.job_type, job_id)
                return
            except Exception as exc:
                job.retry_count = attempt + 1
                await self._append_log(job, f"Attempt {attempt + 1} failed: {exc}")
                logger.warning("Job %s attempt %d failed: %s", job_id, attempt + 1, exc)
                if attempt < job.max_retries:
                    job.status = "retrying"
                    await self.session.flush()
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                else:
                    job.status = "failed"
                    job.error_message = str(exc)
                    job.completed_at = datetime.now(timezone.utc)
                    await self._append_log(job, f"Job failed after {job.max_retries + 1} attempts.")
                    await self.session.commit()
                    logger.error("Job permanently failed: %s (id=%s): %s", job.job_type, job_id, exc)
                    return

    async def cancel(self, job_id: UUID, owner_id: UUID | None = None) -> bool:
        """Cancel a pending or retrying job."""
        job = await self.session.get(BackgroundJob, job_id)
        if not job:
            return False
        if owner_id and job.owner_id != owner_id:
            return False
        if job.status not in ("pending", "retrying"):
            return False
        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        logger.info("Job cancelled: %s (id=%s)", job.job_type, job_id)
        return True

    async def update_progress(self, job_id: UUID, progress: float, message: str | None = None) -> None:
        await self._repo.update_progress(job_id, progress, message)

    async def list_jobs(
        self,
        organization_id: UUID,
        status: str | None = None,
        job_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[BackgroundJob], int]:
        return await self._repo.list_by_org(organization_id, status=status, job_type=job_type, skip=skip, limit=limit)

    async def get_job(self, job_id: UUID) -> BackgroundJob | None:
        return await self.session.get(BackgroundJob, job_id)

    async def _append_log(self, job: BackgroundJob, message: str) -> None:
        logs = list(job.logs or [])
        logs.append({"ts": datetime.now(timezone.utc).isoformat(), "msg": message})
        job.logs = logs[-200:]
        await self.session.flush()
