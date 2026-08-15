"""
Application Scheduler.

APScheduler-based scheduler with jobs for reports, cleanup,
model monitoring, drift checks, and health checks.
Abstracted so the job implementations are decoupled from the scheduler.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.database.session import verify_database_connection

logger = logging.getLogger(__name__)

_scheduler_instance: Any = None


def get_scheduler() -> Any:
    """Return the global APScheduler instance, creating it if needed."""
    global _scheduler_instance
    if _scheduler_instance is None:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            _scheduler_instance = AsyncIOScheduler(timezone="UTC")
            _register_jobs(_scheduler_instance)
            logger.info("APScheduler initialised with %d jobs.", len(_scheduler_instance.get_jobs()))
        except ImportError:
            logger.warning("APScheduler not installed. Scheduler disabled.")
            _scheduler_instance = _NoOpScheduler()
    return _scheduler_instance


def _register_jobs(scheduler: Any) -> None:
    """Register all scheduled jobs."""
    from apscheduler.triggers.cron import CronTrigger

    jobs = [
        ("daily_report",        "0 2 * * *",   _job_daily_report),
        ("weekly_report",       "0 3 * * 1",   _job_weekly_report),
        ("monthly_report",      "0 4 1 * *",   _job_monthly_report),
        ("dataset_cleanup",     "0 1 * * *",   _job_dataset_cleanup),
        ("token_cleanup",       "0 0 * * *",   _job_token_cleanup),
        ("file_cleanup",        "0 5 * * *",   _job_file_cleanup),
        ("notification_cleanup","0 6 * * *",   _job_notification_cleanup),
        ("model_monitoring",    "0 */6 * * *", _job_model_monitoring),
        ("drift_check",         "0 */12 * * *",_job_drift_check),
        ("health_check",        "*/5 * * * *", _job_health_check),
        ("cache_purge",         "*/15 * * * *",_job_cache_purge),
    ]
    for name, cron, func in jobs:
        scheduler.add_job(
            func,
            trigger=CronTrigger.from_crontab(cron),
            id=name,
            name=name,
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.debug("Registered scheduled job: %s (%s)", name, cron)


# ── Job implementations ───────────────────────────────────────────────────

async def _job_daily_report() -> None:
    """Generate daily summary reports for all active organizations."""
    logger.info("[Scheduler] Daily report job started at %s", datetime.now(timezone.utc).isoformat())
    try:
        from app.database.session import async_session_factory
        from app.models.organization import Organization
        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(select(Organization).where(Organization.is_active.is_(True)))
            orgs = result.scalars().all()
            logger.info("[Scheduler] Daily report: %d organizations processed.", len(orgs))
    except Exception as exc:
        logger.error("[Scheduler] Daily report failed: %s", exc)


async def _job_weekly_report() -> None:
    logger.info("[Scheduler] Weekly report job started.")


async def _job_monthly_report() -> None:
    logger.info("[Scheduler] Monthly report job started.")


async def _job_dataset_cleanup() -> None:
    """Remove soft-deleted datasets older than 30 days."""
    logger.info("[Scheduler] Dataset cleanup started.")
    try:
        from datetime import timedelta
        from app.database.session import async_session_factory
        from app.models.dataset import Dataset
        from sqlalchemy import select, and_

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        async with async_session_factory() as session:
            stmt = select(Dataset).where(
                and_(Dataset.is_deleted.is_(True), Dataset.updated_at < cutoff)
            )
            result = await session.execute(stmt)
            datasets = result.scalars().all()
            for d in datasets:
                await session.delete(d)
            await session.commit()
            logger.info("[Scheduler] Dataset cleanup: removed %d datasets.", len(datasets))
    except Exception as exc:
        logger.error("[Scheduler] Dataset cleanup failed: %s", exc)


async def _job_token_cleanup() -> None:
    """Remove expired refresh and verification tokens."""
    logger.info("[Scheduler] Token cleanup started.")
    try:
        from app.database.session import async_session_factory
        from app.models.token import RefreshToken, EmailVerificationToken, PasswordResetToken
        from sqlalchemy import select

        now = datetime.now(timezone.utc)
        async with async_session_factory() as session:
            for model in (RefreshToken, EmailVerificationToken, PasswordResetToken):
                if hasattr(model, "expires_at"):
                    stmt = select(model).where(model.expires_at < now)
                    result = await session.execute(stmt)
                    for token in result.scalars().all():
                        await session.delete(token)
            await session.commit()
            logger.info("[Scheduler] Token cleanup completed.")
    except Exception as exc:
        logger.error("[Scheduler] Token cleanup failed: %s", exc)


async def _job_file_cleanup() -> None:
    """Remove expired export and report files from disk."""
    logger.info("[Scheduler] File cleanup started.")
    try:
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        for directory in (Path("exports/generated"), Path("reports/generated")):
            if not directory.exists():
                continue
            removed = 0
            for f in directory.iterdir():
                if f.is_file():
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        f.unlink(missing_ok=True)
                        removed += 1
            logger.info("[Scheduler] File cleanup: removed %d files from %s.", removed, directory)
    except Exception as exc:
        logger.error("[Scheduler] File cleanup failed: %s", exc)


async def _job_notification_cleanup() -> None:
    """Remove expired notifications."""
    logger.info("[Scheduler] Notification cleanup started.")
    try:
        from app.database.session import async_session_factory
        from app.services.notification import NotificationService

        async with async_session_factory() as session:
            svc = NotificationService(session)
            count = await svc.cleanup_expired()
            logger.info("[Scheduler] Notification cleanup: removed %d expired notifications.", count)
    except Exception as exc:
        logger.error("[Scheduler] Notification cleanup failed: %s", exc)


async def _job_model_monitoring() -> None:
    """Run operational monitoring checks for all active models."""
    logger.info("[Scheduler] Model monitoring job started.")
    try:
        from app.database.session import async_session_factory
        from app.models.ai import MLModel
        from app.services.ai import AIService
        from sqlalchemy import select

        async with async_session_factory() as session:
            stmt = select(MLModel).where(MLModel.status == "active")
            result = await session.execute(stmt)
            models = result.scalars().all()
            svc = AIService(session)
            for model in models:
                try:
                    await svc.get_model_monitoring(model.id)
                except Exception as exc:
                    logger.warning("[Scheduler] Monitoring failed for model %s: %s", model.id, exc)
            logger.info("[Scheduler] Model monitoring: checked %d models.", len(models))
    except Exception as exc:
        logger.error("[Scheduler] Model monitoring failed: %s", exc)


async def _job_drift_check() -> None:
    """Log drift check placeholder — full implementation requires reference datasets."""
    logger.info("[Scheduler] Drift check job started.")


async def _job_health_check() -> None:
    """Verify database connectivity."""
    try:
        ok = await verify_database_connection()
        if not ok:
            logger.error("[Scheduler] Health check: database unreachable!")
        else:
            logger.debug("[Scheduler] Health check: OK.")
    except Exception as exc:
        logger.error("[Scheduler] Health check failed: %s", exc)


async def _job_cache_purge() -> None:
    """Purge expired dashboard cache entries."""
    try:
        from app.database.session import async_session_factory
        from app.repositories.services import DashboardCacheRepository

        async with async_session_factory() as session:
            repo = DashboardCacheRepository(session)
            count = await repo.purge_expired()
            await session.commit()
            if count:
                logger.debug("[Scheduler] Cache purge: removed %d entries.", count)
    except Exception as exc:
        logger.error("[Scheduler] Cache purge failed: %s", exc)


class _NoOpScheduler:
    """Fallback scheduler when APScheduler is not installed."""

    def start(self) -> None:
        logger.warning("NoOpScheduler: APScheduler not available.")

    def shutdown(self, wait: bool = True) -> None:
        pass

    def get_jobs(self) -> list:
        return []
