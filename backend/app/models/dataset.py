"""
Dataset, DatasetVersion, UploadedFile, ProcessingJob, and ValidationReport models.

Defines the complete data model for the dataset ingestion module, including
file storage metadata, versioning, processing lifecycle, and validation results.
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


class Dataset(BaseModel):
    """Top-level dataset entity owned by a user within an organization."""

    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(
        String(256), nullable=False, index=True,
        comment="Display name of the dataset.",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Optional description of the dataset.",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="Foreign key to the user who owns this dataset.",
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="Foreign key to the organization that owns this dataset.",
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, nullable=True,
        comment="Foreign key to the currently active DatasetVersion.",
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Soft-delete flag.",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp when the dataset was soft-deleted.",
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    versions = relationship(
        "DatasetVersion", back_populates="dataset",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name})>"


class DatasetVersion(BaseModel):
    """A specific version of a dataset."""

    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version"),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, nullable=True,
        comment="Foreign key to the ValidationReport for this version.",
    )

    dataset = relationship("Dataset", back_populates="versions")
    files = relationship(
        "UploadedFile", back_populates="version",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DatasetVersion(dataset={self.dataset_id}, version={self.version_number})>"


class UploadedFile(BaseModel):
    """Stored file metadata for a dataset version."""

    __tablename__ = "uploaded_files"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Timestamp when the file was uploaded.",
    )

    version = relationship("DatasetVersion", back_populates="files")

    def __repr__(self) -> str:
        return f"<UploadedFile(name={self.original_filename}, size={self.file_size})>"


class DatasetMetadata(BaseModel):
    """Extracted metadata for a dataset version."""

    __tablename__ = "dataset_metadata"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_id", name="uq_dataset_metadata"),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_names: Mapped[list] = mapped_column(JSON, nullable=True)
    column_types: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    null_counts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    distinct_counts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    memory_usage_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    encoding: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Timestamp when metadata was extracted.",
    )

    def __repr__(self) -> str:
        return f"<DatasetMetadata(dataset={self.dataset_id}, rows={self.row_count})>"


class ProcessingJob(BaseModel):
    """Background processing job lifecycle tracking."""

    __tablename__ = "processing_jobs"

    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, nullable=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="One of: upload, validation, metadata_extraction, quality_scoring.",
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True,
        comment="One of: pending, running, completed, failed.",
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ProcessingJob(dataset={self.dataset_id}, type={self.job_type}, status={self.status})>"


class ValidationReport(BaseModel):
    """Data quality validation results for a dataset version."""

    __tablename__ = "validation_reports"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, nullable=True,
    )
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    validity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    uniqueness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    issues: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    column_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Timestamp when the report was generated.",
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ValidationReport(dataset={self.dataset_id}, score={self.quality_score})>"