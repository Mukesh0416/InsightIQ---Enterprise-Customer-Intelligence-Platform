"""
Notification Engine.

Delivers in-app notifications with email-ready and webhook-ready abstractions.
Manages preferences, history, unread counts, and expiration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.services import Notification, NotificationPreference
from app.repositories.services import NotificationRepository

logger = logging.getLogger(__name__)

_DEFAULT_EXPIRY_DAYS = 30

# ── Notification type constants ───────────────────────────────────────────
class NotificationType:
    DATASET_PROCESSED = "dataset_processed"
    TRAINING_COMPLETED = "training_completed"
    PREDICTION_COMPLETED = "prediction_completed"
    REPORT_READY = "report_ready"
    DRIFT_DETECTED = "drift_detected"
    MODEL_FAILURE = "model_failure"
    SYSTEM_ALERT = "system_alert"
    INVITATION = "invitation"
    PASSWORD_EVENT = "password_event"
    EXPORT_COMPLETED = "export_completed"
    JOB_FAILED = "job_failed"


# ── Template registry ─────────────────────────────────────────────────────
_TEMPLATES: dict[str, dict[str, str]] = {
    NotificationType.DATASET_PROCESSED: {
        "title": "Dataset Processing Completed",
        "message": "Your dataset '{name}' has been processed successfully.",
        "priority": "normal",
    },
    NotificationType.TRAINING_COMPLETED: {
        "title": "Model Training Completed",
        "message": "Experiment '{name}' finished. Best algorithm: {algorithm} (score: {score}).",
        "priority": "normal",
    },
    NotificationType.PREDICTION_COMPLETED: {
        "title": "Batch Prediction Completed",
        "message": "Batch prediction job '{name}' processed {count} records.",
        "priority": "normal",
    },
    NotificationType.REPORT_READY: {
        "title": "Report Ready for Download",
        "message": "Your {report_type} report '{name}' is ready.",
        "priority": "normal",
    },
    NotificationType.DRIFT_DETECTED: {
        "title": "Data Drift Detected",
        "message": "Significant drift detected for model '{name}' (score: {score:.2f}). Retraining recommended.",
        "priority": "high",
    },
    NotificationType.MODEL_FAILURE: {
        "title": "Model Failure Alert",
        "message": "Model '{name}' encountered a failure: {error}",
        "priority": "critical",
    },
    NotificationType.SYSTEM_ALERT: {
        "title": "System Alert",
        "message": "{message}",
        "priority": "high",
    },
    NotificationType.EXPORT_COMPLETED: {
        "title": "Export Ready",
        "message": "Your {format} export is ready for download.",
        "priority": "normal",
    },
    NotificationType.JOB_FAILED: {
        "title": "Background Job Failed",
        "message": "Job '{job_type}' failed after {retries} retries: {error}",
        "priority": "high",
    },
    NotificationType.INVITATION: {
        "title": "Invitation Received",
        "message": "You have been invited to join the organization '{organization_name}'.",
        "priority": "normal",
    },
    NotificationType.PASSWORD_EVENT: {
        "title": "Security Notice",
        "message": "A password-related event occurred for your account.",
        "priority": "normal",
    },
}


class NotificationService:
    """Manages notification creation, delivery, and preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = NotificationRepository(session)

    async def send(
        self,
        user_id: UUID,
        notification_type: str,
        template_vars: dict[str, Any] | None = None,
        *,
        organization_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action_url: str | None = None,
        metadata: dict | None = None,
        expiry_days: int = _DEFAULT_EXPIRY_DAYS,
        override_title: str | None = None,
        override_message: str | None = None,
        override_priority: str | None = None,
    ) -> Notification:
        """
        Create and persist a notification using a template.

        Checks user preferences before delivery.
        Dispatches to email/webhook channels if configured.
        """
        pref = await self._repo.get_preference(user_id)
        if pref and not pref.in_app_enabled:
            logger.debug("In-app notifications disabled for user %s", user_id)

        tmpl = _TEMPLATES.get(notification_type, {
            "title": notification_type.replace("_", " ").title(),
            "message": str(template_vars or {}),
            "priority": "normal",
        })
        vars_ = template_vars or {}
        title = override_title or tmpl["title"]
        try:
            message = override_message or tmpl["message"].format(**vars_)
        except KeyError:
            message = override_message or tmpl["message"]
        priority = override_priority or tmpl["priority"]

        delivered_via = ["in_app"]

        # Email dispatch (abstraction — plug in SMTP/SES here)
        if pref is None or pref.email_enabled:
            self._dispatch_email(user_id, title, message, notification_type)
            delivered_via.append("email")

        # Webhook dispatch (abstraction)
        if pref and pref.webhook_enabled and pref.webhook_url:
            self._dispatch_webhook(pref.webhook_url, notification_type, title, message, vars_)
            delivered_via.append("webhook")

        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            action_url=action_url,
            metadata_json=metadata,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
            delivered_via=delivered_via,
        )
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        logger.info("Notification sent: type=%s user=%s priority=%s", notification_type, user_id, priority)
        return notification

    async def list_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        return await self._repo.list_for_user(user_id, unread_only=unread_only, skip=skip, limit=limit)

    async def unread_count(self, user_id: UUID) -> int:
        return await self._repo.unread_count(user_id)

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        await self._repo.mark_read(notification_id, user_id)
        await self.session.commit()

    async def mark_all_read(self, user_id: UUID) -> int:
        count = await self._repo.mark_all_read(user_id)
        await self.session.commit()
        return count

    async def delete(self, notification_id: UUID, user_id: UUID) -> None:
        notif = await self.session.get(Notification, notification_id)
        if notif and notif.user_id == user_id:
            await self.session.delete(notif)
            await self.session.commit()

    async def get_or_create_preference(self, user_id: UUID) -> NotificationPreference:
        pref = await self._repo.get_preference(user_id)
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            self.session.add(pref)
            await self.session.flush()
            await self.session.refresh(pref)
        return pref

    async def update_preference(self, user_id: UUID, updates: dict[str, Any]) -> NotificationPreference:
        pref = await self.get_or_create_preference(user_id)
        for key, value in updates.items():
            if hasattr(pref, key) and value is not None:
                setattr(pref, key, value)
        await self.session.commit()
        return pref

    async def cleanup_expired(self) -> int:
        count = await self._repo.delete_expired()
        await self.session.commit()
        return count

    # ── Channel abstractions ──────────────────────────────────────────────

    def _dispatch_email(self, user_id: UUID, title: str, message: str, notification_type: str) -> None:
        """
        Email dispatch abstraction.
        Replace with SMTP/SES/SendGrid implementation.
        """
        logger.debug("Email dispatch (stub): user=%s type=%s title=%s", user_id, notification_type, title)

    def _dispatch_webhook(self, url: str, notification_type: str, title: str, message: str, data: dict) -> None:
        """
        Webhook dispatch abstraction.
        Replace with httpx async POST implementation.
        """
        logger.debug("Webhook dispatch (stub): url=%s type=%s", url, notification_type)
