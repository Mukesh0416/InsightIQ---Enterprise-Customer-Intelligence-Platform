"""
Pydantic v2 schemas for the Application Services Layer.

Covers dashboard, reports, exports, notifications, jobs, audit, activity, search.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Dashboard ─────────────────────────────────────────────────────────────

class DashboardFilters(BaseModel):
    dataset_id: UUID | None = None
    organization_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class KPICard(BaseModel):
    label: str
    value: Any
    unit: str | None = None
    change_pct: float | None = None
    trend: str | None = None  # up | down | flat
    icon: str | None = None


class WidgetRequest(BaseModel):
    widget_type: str = Field(
        description="kpi_card | table | line_chart | area_chart | bar_chart | pie_chart | heatmap | scatter | box_plot | treemap | waterfall | funnel | radar | correlation_matrix"
    )
    dataset_id: UUID
    config: dict[str, Any] = Field(default_factory=dict)


# ── Reports ───────────────────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    report_type: str = Field(
        description="executive | business | eda | quality | customer | revenue | sales | retention | prediction | model | drift"
    )
    format: str = Field(pattern="^(pdf|excel|csv|json)$")
    dataset_id: UUID
    organization_id: UUID | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        valid = {"executive", "business", "eda", "quality", "customer", "revenue", "sales", "retention", "prediction", "model", "drift"}
        if v not in valid:
            raise ValueError(f"Invalid report_type. Must be one of: {valid}")
        return v


class ReportResponse(BaseModel):
    id: UUID
    name: str
    report_type: str
    format: str
    status: str
    dataset_id: UUID | None
    organization_id: UUID | None
    owner_id: UUID | None
    file_size_bytes: int | None
    download_count: int
    error_message: str | None
    generated_at: datetime | None
    generation_duration_ms: float | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Exports ───────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    export_type: str = Field(description="dashboard | analytics | predictions | table | report")
    format: str = Field(pattern="^(csv|excel|pdf|json)$")
    dataset_id: UUID | None = None
    organization_id: UUID | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class ExportResponse(BaseModel):
    id: UUID
    export_type: str
    format: str
    status: str
    file_size_bytes: int | None
    row_count: int | None
    error_message: str | None
    expires_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Notifications ─────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str
    priority: str
    is_read: bool
    read_at: datetime | None
    resource_type: str | None
    resource_id: str | None
    action_url: str | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None
    webhook_enabled: bool | None = None
    webhook_url: str | None = None
    type_preferences: dict[str, bool] | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


# ── Background Jobs ───────────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: UUID
    job_type: str
    status: str
    priority: int
    progress: float
    progress_message: str | None
    error_message: str | None
    retry_count: int
    max_retries: int
    started_at: datetime | None
    completed_at: datetime | None
    scheduled_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Audit ─────────────────────────────────────────────────────────────────

class AuditEventResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    organization_id: UUID | None
    event_category: str
    event_type: str
    action: str
    resource_type: str | None
    resource_id: str | None
    resource_name: str | None
    severity: str
    ip_address: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Activity ──────────────────────────────────────────────────────────────

class ActivityLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    organization_id: UUID | None
    activity_type: str
    title: str
    description: str | None
    resource_type: str | None
    resource_id: str | None
    resource_name: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Search ────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    description: str | None
    score: float
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResult]
    suggestions: list[str]
    took_ms: float
