"""
ORM models for the Application Services Layer.

Covers Report, ExportJob, Notification, NotificationPreference,
BackgroundJob, ScheduledTask, AuditEvent, ActivityLog, DashboardCache.
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.types import UUID
from app.models.base import BaseModel


class Report(BaseModel):
    """Generated report record with metadata and download tracking."""

    __tablename__ = "reports"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="executive | business | eda | quality | customer | revenue | sales | retention | prediction | model | drift",
    )
    format: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="pdf | excel | csv | json",
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="pending | generating | completed | failed",
    )
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
        nullable=True, index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="Report generation parameters")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generation_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class ExportJob(BaseModel):
    """Asynchronous data export job tracking."""

    __tablename__ = "export_jobs"

    export_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="dashboard | analytics | predictions | table | report",
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False, comment="csv | excel | pdf | json")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="pending | running | completed | failed",
    )
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
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(BaseModel):
    """In-app notification with priority, read state, and expiration."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    notification_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="dataset_processed | training_completed | prediction_completed | report_ready | drift_detected | model_failure | system_alert | invitation | password_event",
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default="normal",
        comment="low | normal | high | critical",
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_via: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="['in_app', 'email', 'webhook']")


class NotificationPreference(BaseModel):
    """Per-user notification channel and type preferences."""

    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_pref_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Per-type toggles stored as JSON: {"dataset_processed": true, ...}
    type_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True, comment="HH:MM")
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True, comment="HH:MM")


class BackgroundJob(BaseModel):
    """Background job lifecycle tracking with retry support."""

    __tablename__ = "background_jobs"

    job_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="report_generation | export | training | batch_prediction | drift_analysis | cleanup",
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="pending | running | completed | failed | cancelled | retrying",
    )
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="1=highest, 10=lowest")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    logs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ScheduledTask(BaseModel):
    """Recurring scheduled task definition."""

    __tablename__ = "scheduled_tasks"
    __table_args__ = (UniqueConstraint("task_name", name="uq_scheduled_task_name"),)

    task_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    task_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="daily_report | weekly_report | monthly_report | dataset_cleanup | token_cleanup | file_cleanup | notification_cleanup | model_monitoring | drift_check | health_check",
    )
    cron_expression: Mapped[str] = mapped_column(String(64), nullable=False, comment="Cron expression e.g. '0 2 * * *'")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_run_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AuditEvent(BaseModel):
    """Detailed audit event for compliance and security tracking."""

    __tablename__ = "audit_events"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    event_category: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="auth | dataset | prediction | training | report | export | role | permission | organization | settings",
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    resource_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="info",
        comment="info | warning | error | critical",
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class ActivityLog(BaseModel):
    """User and system activity feed entries."""

    __tablename__ = "activity_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    activity_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="user | organization | dataset | ai | report | notification",
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class DashboardCache(BaseModel):
    """Cached dashboard widget data with TTL."""

    __tablename__ = "dashboard_cache"
    __table_args__ = (
        UniqueConstraint("cache_key", name="uq_dashboard_cache_key"),
    )

    cache_key: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    widget_type: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)