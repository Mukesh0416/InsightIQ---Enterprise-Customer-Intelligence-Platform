"""Pydantic schemas for dataset management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256, description="Dataset display name.")
    description: str | None = Field(None, description="Optional dataset description.")


class UploadFileResponse(BaseModel):
    original_filename: str = Field(..., description="Original uploaded filename.")
    stored_filename: str = Field(..., description="Stored filename on disk.")
    file_size: int = Field(..., description="File size in bytes.")
    checksum_sha256: str = Field(..., description="SHA-256 checksum of the file.")
    mime_type: str | None = Field(None, description="Detected MIME type.")
    file_extension: str = Field(..., description="File extension (e.g. .csv).")
    storage_provider: str = Field("local", description="Storage backend used.")
    upload_timestamp: datetime = Field(..., description="Upload timestamp.")


class DatasetReadResponse(BaseModel):
    id: UUID = Field(..., description="Dataset UUID.")
    name: str = Field(..., description="Dataset name.")
    description: str | None = Field(None, description="Dataset description.")
    owner_id: UUID = Field(..., description="Owner user UUID.")
    organization_id: UUID | None = Field(None, description="Organization UUID.")
    current_version_id: UUID | None = Field(None, description="Active version UUID.")
    is_deleted: bool = Field(..., description="Soft-delete flag.")
    row_count: int = Field(0, description="Number of rows.")
    column_count: int = Field(0, description="Number of columns.")
    quality_score: float = Field(0.0, description="Data quality score (0–100).")
    total_size_bytes: int = Field(0, description="Total stored size in bytes.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class DatasetListResponse(BaseModel):
    items: list[DatasetReadResponse] = Field(..., description="List of datasets.")
    total: int = Field(..., description="Total count.")
    page: int = Field(..., description="Current page.")
    page_size: int = Field(..., description="Items per page.")
    total_pages: int = Field(..., description="Total pages.")


class DatasetVersionResponse(BaseModel):
    id: UUID = Field(..., description="Version UUID.")
    dataset_id: UUID = Field(..., description="Dataset UUID.")
    version_number: int = Field(..., description="Version number (1-based).")
    is_current: bool = Field(..., description="Whether this is the active version.")
    created_by: UUID = Field(..., description="User who created this version.")
    commit_message: str | None = Field(None, description="Version commit message.")
    row_count: int = Field(0, description="Row count.")
    column_count: int = Field(0, description="Column count.")
    quality_score: float = Field(0.0, description="Quality score (0–100).")
    created_at: datetime = Field(..., description="Version creation timestamp.")


class DatasetPreviewResponse(BaseModel):
    dataset_id: UUID = Field(..., description="Dataset UUID.")
    version_id: UUID = Field(..., description="Version UUID.")
    columns: list[str] = Field(..., description="Column names.")
    rows: list[list[Any]] = Field(..., description="First 100 rows as nested lists.")
    row_count: int = Field(..., description="Total row count in dataset.")
    column_types: dict[str, str] = Field(..., description="Detected column types.")


class DatasetMetadataResponse(BaseModel):
    dataset_id: UUID = Field(..., description="Dataset UUID.")
    version_id: UUID = Field(..., description="Version UUID.")
    row_count: int = Field(..., description="Number of rows.")
    column_count: int = Field(..., description="Number of columns.")
    column_names: list[str] = Field(..., description="Column names.")
    column_types: dict[str, str] = Field(..., description="Detected column types.")
    null_counts: dict[str, int] = Field(..., description="Null counts per column.")
    distinct_counts: dict[str, int] = Field(..., description="Distinct counts per column.")
    memory_usage_bytes: int = Field(..., description="Estimated memory usage.")
    file_size: int = Field(..., description="Source file size.")
    encoding: str | None = Field(None, description="Detected file encoding.")
    extracted_at: datetime = Field(..., description="Metadata extraction timestamp.")


class ValidationReportResponse(BaseModel):
    dataset_id: UUID = Field(..., description="Dataset UUID.")
    version_id: UUID | None = Field(None, description="Version UUID.")
    quality_score: float = Field(..., description="Overall quality score (0–100).")
    completeness: float = Field(..., description="Completeness score.")
    consistency: float = Field(..., description="Consistency score.")
    validity: float = Field(..., description="Validity score.")
    uniqueness: float = Field(..., description="Uniqueness score.")
    accuracy: float = Field(..., description="Accuracy score.")
    issues: list[dict[str, Any]] = Field(default_factory=list, description="Detected issues.")
    column_summary: dict[str, Any] | None = Field(None, description="Per-column summary.")
    is_valid: bool = Field(True, description="Whether the dataset passed validation.")


class NewVersionRequest(BaseModel):
    commit_message: str | None = Field(None, max_length=500, description="Commit message for this version.")