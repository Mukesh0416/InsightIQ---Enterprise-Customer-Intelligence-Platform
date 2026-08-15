"""
Repository layer for the Application Services module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.services import (
    ActivityLog,
    AuditEvent,
    BackgroundJob,
    DashboardCache,
    Notification,
    NotificationPreference,
    Report,
)


# ── Report Repository ─────────────────────────────────────────────────────

class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        stmt = select(Report).where(Report.organization_id == organization_id)
        count_stmt = select(func.count(Report.id)).where(Report.organization_id == organization_id)
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_by_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        stmt = select(Report).where(Report.owner_id == owner_id)
        count_stmt = select(func.count(Report.id)).where(Report.owner_id == owner_id)
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def increment_download(self, report_id: UUID) -> None:
        await self.session.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(download_count=Report.download_count + 1)
        )


# ── Export Job Repository ────────────────────────────────────────────────

class ExportJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


# ── Notification Repository ──────────────────────────────────────────────

class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
            count_stmt = count_stmt.where(Notification.is_read.is_(False))
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def unread_count(self, user_id: UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        return result.rowcount or 0

    async def get_preference(self, user_id: UUID) -> NotificationPreference | None:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            delete(Notification).where(Notification.expires_at < now)
        )
        return result.rowcount or 0


# ── Background Job Repository ────────────────────────────────────────────

class BackgroundJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(
        self,
        organization_id: UUID,
        status: str | None = None,
        job_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[BackgroundJob], int]:
        stmt = select(BackgroundJob).where(BackgroundJob.organization_id == organization_id)
        count_stmt = select(func.count(BackgroundJob.id)).where(BackgroundJob.organization_id == organization_id)
        if status:
            stmt = stmt.where(BackgroundJob.status == status)
            count_stmt = count_stmt.where(BackgroundJob.status == status)
        if job_type:
            stmt = stmt.where(BackgroundJob.job_type == job_type)
            count_stmt = count_stmt.where(BackgroundJob.job_type == job_type)
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(BackgroundJob.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update_progress(self, job_id: UUID, progress: float, message: str | None = None) -> None:
        values: dict[str, Any] = {"progress": progress}
        if message:
            values["progress_message"] = message
        await self.session.execute(update(BackgroundJob).where(BackgroundJob.id == job_id).values(**values))


# ── Audit Event Repository ───────────────────────────────────────────────

class AuditEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
        event_category: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
        severity: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        stmt = select(AuditEvent)
        count_stmt = select(func.count(AuditEvent.id))
        if organization_id:
            stmt = stmt.where(AuditEvent.organization_id == organization_id)
            count_stmt = count_stmt.where(AuditEvent.organization_id == organization_id)
        if user_id:
            stmt = stmt.where(AuditEvent.user_id == user_id)
            count_stmt = count_stmt.where(AuditEvent.user_id == user_id)
        if event_category:
            stmt = stmt.where(AuditEvent.event_category == event_category)
            count_stmt = count_stmt.where(AuditEvent.event_category == event_category)
        if event_type:
            stmt = stmt.where(AuditEvent.event_type == event_type)
            count_stmt = count_stmt.where(AuditEvent.event_type == event_type)
        if resource_type:
            stmt = stmt.where(AuditEvent.resource_type == resource_type)
            count_stmt = count_stmt.where(AuditEvent.resource_type == resource_type)
        if severity:
            stmt = stmt.where(AuditEvent.severity == severity)
            count_stmt = count_stmt.where(AuditEvent.severity == severity)
        if date_from:
            stmt = stmt.where(AuditEvent.timestamp >= date_from)
            count_stmt = count_stmt.where(AuditEvent.timestamp >= date_from)
        if date_to:
            stmt = stmt.where(AuditEvent.timestamp <= date_to)
            count_stmt = count_stmt.where(AuditEvent.timestamp <= date_to)
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total


# ── Activity Log Repository ──────────────────────────────────────────────

class ActivityLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_org(
        self,
        organization_id: UUID,
        activity_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ActivityLog], int]:
        stmt = select(ActivityLog).where(ActivityLog.organization_id == organization_id)
        count_stmt = select(func.count(ActivityLog.id)).where(ActivityLog.organization_id == organization_id)
        if activity_type:
            stmt = stmt.where(ActivityLog.activity_type == activity_type)
            count_stmt = count_stmt.where(ActivityLog.activity_type == activity_type)
        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(
            stmt.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total


# ── Dashboard Cache Repository ───────────────────────────────────────────

class DashboardCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_key(self, key: str) -> DashboardCache | None:
        stmt = select(DashboardCache).where(
            DashboardCache.cache_key == key,
            DashboardCache.expires_at > datetime.now(timezone.utc),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def set(
        self,
        key: str,
        data: dict[str, Any],
        widget_type: str,
        expires_at: datetime,
        organization_id: UUID | None = None,
        dataset_id: UUID | None = None,
    ) -> None:
        existing = await self.get_by_key(key)
        if existing:
            existing.data = data
            existing.expires_at = expires_at
        else:
            self.session.add(DashboardCache(
                cache_key=key,
                data=data,
                widget_type=widget_type,
                expires_at=expires_at,
                organization_id=organization_id,
                dataset_id=dataset_id,
            ))

    async def invalidate_for_dataset(self, dataset_id: UUID) -> None:
        await self.session.execute(
            delete(DashboardCache).where(DashboardCache.dataset_id == dataset_id)
        )

    async def purge_expired(self) -> int:
        result = await self.session.execute(
            delete(DashboardCache).where(DashboardCache.expires_at < datetime.now(timezone.utc))
        )
        return result.rowcount or 0