"""
Audit Service.

Records all security-relevant and compliance events to the AuditEvent table.
Also writes ActivityLog entries for the user-facing activity feed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.services import ActivityLog, AuditEvent
from app.repositories.services import ActivityLogRepository, AuditEventRepository

logger = logging.getLogger(__name__)

# Canonical event type constants
class AuditEventType:
    # Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    PASSWORD_CHANGED = "user.password_changed"
    PASSWORD_RESET = "user.password_reset"
    # Dataset
    DATASET_UPLOADED = "dataset.uploaded"
    DATASET_DELETED = "dataset.deleted"
    DATASET_UPDATED = "dataset.updated"
    # AI
    TRAINING_STARTED = "ai.training_started"
    TRAINING_COMPLETED = "ai.training_completed"
    PREDICTION_REQUESTED = "ai.prediction_requested"
    MODEL_ACTIVATED = "ai.model_activated"
    MODEL_ARCHIVED = "ai.model_archived"
    # Reports
    REPORT_GENERATED = "report.generated"
    REPORT_DOWNLOADED = "report.downloaded"
    REPORT_DELETED = "report.deleted"
    # Exports
    EXPORT_REQUESTED = "export.requested"
    EXPORT_COMPLETED = "export.completed"
    # RBAC
    ROLE_CHANGED = "rbac.role_changed"
    PERMISSION_CHANGED = "rbac.permission_changed"
    # Organization
    ORG_MEMBER_ADDED = "organization.member_added"
    ORG_MEMBER_REMOVED = "organization.member_removed"
    ORG_SETTINGS_CHANGED = "organization.settings_changed"
    # Settings
    SETTINGS_CHANGED = "settings.changed"


class AuditService:
    """Records audit events and activity log entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._audit_repo = AuditEventRepository(session)
        self._activity_repo = ActivityLogRepository(session)

    async def record(
        self,
        event_type: str,
        action: str,
        event_category: str,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_name: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        severity: str = "info",
    ) -> AuditEvent:
        """Persist an audit event record."""
        event = AuditEvent(
            user_id=user_id,
            organization_id=organization_id,
            event_category=event_category,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            old_value=old_value,
            new_value=new_value,
            metadata_json=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
        )
        self.session.add(event)
        await self.session.flush()
        logger.info("Audit event: %s | user=%s | resource=%s/%s", event_type, user_id, resource_type, resource_id)
        return event

    async def log_activity(
        self,
        title: str,
        activity_type: str,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        description: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_name: str | None = None,
        metadata: dict | None = None,
    ) -> ActivityLog:
        """Persist an activity feed entry."""
        entry = ActivityLog(
            user_id=user_id,
            organization_id=organization_id,
            activity_type=activity_type,
            title=title,
            description=description,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            metadata_json=metadata,
            timestamp=datetime.now(timezone.utc),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def search_events(
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
        return await self._audit_repo.search(
            organization_id=organization_id,
            user_id=user_id,
            event_category=event_category,
            event_type=event_type,
            resource_type=resource_type,
            severity=severity,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )

    async def get_activity_feed(
        self,
        organization_id: UUID,
        activity_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ActivityLog], int]:
        return await self._activity_repo.list_for_org(
            organization_id=organization_id,
            activity_type=activity_type,
            skip=skip,
            limit=limit,
        )
