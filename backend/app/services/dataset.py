"""
Dataset service implementing upload, validation, metadata extraction,
quality scoring, versioning, and lifecycle business logic.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.dataset import (
    Dataset,
    DatasetMetadata,
    DatasetVersion,
    ProcessingJob,
    UploadedFile,
    ValidationReport,
)
from app.repositories.dataset import DatasetRepository
from app.storage import get_storage_provider
from app.validators.column_validator import ColumnValidator
from app.validators.file_validator import FileValidator
from app.validators.quality_engine import QualityEngine
from app.validators.type_detector import TypeDetector

logger = logging.getLogger(__name__)


class DatasetService:
    """Orchestrates dataset ingestion, validation, and versioning."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DatasetRepository(session)
        self.file_validator = FileValidator()
        self.storage = get_storage_provider()

    async def upload(
        self,
        filename: str,
        data: bytes,
        owner_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        name: str | None = None,
        description: str | None = None,
    ) -> Dataset:
        """Validate, store, and process an uploaded dataset file."""
        logger.info("Upload started: %s", filename)

        # Validate file
        safe_name = self.file_validator.validate_filename(filename)
        ext = self.file_validator.validate_extension(safe_name)
        self.file_validator.validate_size(len(data))
        checksum = self.file_validator.compute_sha256(data)

        # Duplicate detection
        existing = await self.repo.find_by_checksum(checksum)
        if existing:
            raise ConflictError("A file with identical content has already been uploaded.")

        # Store file
        unique_id = str(uuid.uuid4())
        stored = await self.storage.save(data, safe_name, unique_id)

        # Create dataset
        dataset = Dataset(
            name=name or Path(safe_name).stem,
            description=description,
            owner_id=owner_id,
            organization_id=organization_id,
            total_size_bytes=len(data),
        )
        self.session.add(dataset)
        await self.session.flush()

        # Parse into DataFrame for validation
        df = self._read_file(data, ext)

        # Column validation
        headers = [str(c) for c in df.columns]
        ColumnValidator.validate_headers(headers)

        # Version 1
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=1,
            is_current=True,
            created_by=owner_id,
            row_count=len(df),
            column_count=len(df.columns),
        )
        self.session.add(version)
        await self.session.flush()

        # Uploaded file record
        uploaded_file = UploadedFile(
            dataset_id=dataset.id,
            version_id=version.id,
            original_filename=safe_name,
            stored_filename=stored.stored_filename,
            file_size=len(data),
            checksum_sha256=checksum,
            mime_type=ext,
            file_extension=ext,
            storage_provider=stored.storage_provider,
            storage_path=stored.storage_path,
            uploaded_by=owner_id,
            upload_timestamp=datetime.now(timezone.utc),
        )
        self.session.add(uploaded_file)

        # Metadata extraction
        metadata = self._extract_metadata(dataset, version, df, len(data))
        self.session.add(metadata)

        # Quality scoring
        quality = QualityEngine.analyze(df)
        report = ValidationReport(
            dataset_id=dataset.id,
            version_id=version.id,
            quality_score=quality["quality_score"],
            completeness_score=quality["completeness"],
            consistency_score=quality["consistency"],
            validity_score=quality["validity"],
            uniqueness_score=quality["uniqueness"],
            accuracy_score=quality["accuracy"],
            issues=quality["issues"],
            column_summary=quality["column_summary"],
            is_valid=quality["quality_score"] >= getattr(settings, "DATASET_MIN_QUALITY_SCORE", 50),
        )
        self.session.add(report)

        # Update dataset aggregates
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.quality_score = quality["quality_score"]
        dataset.current_version_id = version.id
        version.quality_score = quality["quality_score"]
        version.metadata_json = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "column_types": metadata.column_types,
        }
        version.validation_report_id = report.id

        await self.session.flush()
        logger.info("Upload completed: %s (rows=%d, cols=%d)", safe_name, len(df), len(df.columns))

        # Create processing job record
        job = ProcessingJob(
            dataset_id=dataset.id,
            version_id=version.id,
            job_type="upload",
            status="completed",
            progress=100.0,
            result={"rows": len(df), "columns": len(df.columns), "quality_score": quality["quality_score"]},
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(job)
        await self.session.flush()

        return dataset

    def _read_file(self, data: bytes, ext: str) -> pd.DataFrame:
        """Read file bytes into a pandas DataFrame based on extension."""
        try:
            if ext == ".csv":
                return pd.read_csv(io.BytesIO(data))
            if ext in (".xlsx", ".xls"):
                return pd.read_excel(io.BytesIO(data))
            raise ValidationError(f"Unsupported file extension: {ext}")
        except pd.errors.EmptyDataError as exc:
            raise ValidationError("Cannot upload an empty file.") from exc
        except pd.errors.ParserError as exc:
            raise ValidationError(f"Unable to parse file: {exc}") from exc
        except Exception as exc:
            raise ValidationError(f"File processing failed: {exc}") from exc

    def _extract_metadata(
        self,
        dataset: Dataset,
        version: DatasetVersion,
        df: pd.DataFrame,
        file_size: int,
    ) -> DatasetMetadata:
        """Extract structural metadata from a DataFrame."""
        null_counts: dict[str, int] = {}
        distinct_counts: dict[str, int] = {}
        for col in df.columns:
            null_counts[str(col)] = int(df[col].isna().sum())
            distinct_counts[str(col)] = int(df[col].nunique())
        return DatasetMetadata(
            dataset_id=dataset.id,
            version_id=version.id,
            row_count=len(df),
            column_count=len(df.columns),
            column_names=[str(c) for c in df.columns],
            column_types=TypeDetector.detect_column_types(df),
            null_counts=null_counts,
            distinct_counts=distinct_counts,
            memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
            file_size=file_size,
            encoding="utf-8",
            extracted_at=datetime.now(timezone.utc),
        )

    async def _get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        dataset = await self.session.get(Dataset, dataset_id)
        if not dataset or dataset.is_deleted:
            raise NotFoundError(f"Dataset {dataset_id} not found.")
        return dataset

    async def get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        return await self._get_dataset(dataset_id)

    async def list_datasets(
        self,
        owner_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Dataset], int]:
        skip = (page - 1) * page_size
        return await self.repo.list_datasets(owner_id, organization_id, query, False, skip, page_size)

    async def delete_dataset(self, dataset_id: uuid.UUID) -> None:
        dataset = await self._get_dataset(dataset_id)
        dataset.is_deleted = True
        dataset.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info("Dataset soft-deleted: %s", dataset_id)

    async def get_versions(self, dataset_id: uuid.UUID) -> list[DatasetVersion]:
        await self._get_dataset(dataset_id)
        return await self.repo.list_versions(dataset_id)

    async def get_preview(self, dataset_id: uuid.UUID, limit: int = 100) -> dict[str, Any]:
        dataset = await self._get_dataset(dataset_id)
        version = await self.repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        file = await self.repo.get_file_by_version(version.id)
        if not file:
            raise NotFoundError("No stored file for current version.")
        data = await self.storage.read(file.storage_path)
        df = self._read_file(data, file.file_extension)
        preview_rows = df.head(limit).where(pd.notnull(df), None)
        return {
            "dataset_id": dataset_id,
            "version_id": version.id,
            "columns": [str(c) for c in df.columns],
            "rows": [list(row) for row in preview_rows.itertuples(index=False)],
            "row_count": len(df),
            "column_types": TypeDetector.detect_column_types(df),
        }

    async def get_metadata(self, dataset_id: uuid.UUID) -> DatasetMetadata:
        dataset = await self._get_dataset(dataset_id)
        version = await self.repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        metadata = await self.session.execute(
            select(DatasetMetadata).where(DatasetMetadata.version_id == version.id)
        )
        md = metadata.scalar_one_or_none()
        if not md:
            raise NotFoundError("Metadata not found for this version.")
        return md

    async def get_validation(self, dataset_id: uuid.UUID) -> ValidationReport:
        dataset = await self._get_dataset(dataset_id)
        version = await self.repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        report = await self.repo.get_validation_report(version.id)
        if not report:
            raise NotFoundError("Validation report not found for this version.")
        return report

    async def download(self, dataset_id: uuid.UUID) -> tuple[bytes, str, str]:
        dataset = await self._get_dataset(dataset_id)
        version = await self.repo.get_current_version(dataset_id)
        if not version:
            raise NotFoundError("Dataset has no current version.")
        file = await self.repo.get_file_by_version(version.id)
        if not file:
            raise NotFoundError("No stored file for current version.")
        data = await self.storage.read(file.storage_path)
        return data, file.original_filename, file.mime_type or "application/octet-stream"

    async def add_version(
        self,
        dataset_id: uuid.UUID,
        filename: str,
        data: bytes,
        owner_id: uuid.UUID,
        commit_message: str | None = None,
    ) -> DatasetVersion:
        dataset = await self._get_dataset(dataset_id)
        safe_name = self.file_validator.validate_filename(filename)
        ext = self.file_validator.validate_extension(safe_name)
        self.file_validator.validate_size(len(data))
        checksum = self.file_validator.compute_sha256(data)
        existing = await self.repo.find_by_checksum(checksum)
        if existing and existing.dataset_id == dataset_id:
            raise ConflictError("This file content already exists for this dataset.")

        unique_id = str(uuid.uuid4())
        stored = await self.storage.save(data, safe_name, unique_id)
        df = self._read_file(data, ext)
        ColumnValidator.validate_headers([str(c) for c in df.columns])

        versions = await self.repo.list_versions(dataset_id)
        next_number = (versions[0].version_number + 1) if versions else 1

        # Mark previous as not current
        current = await self.repo.get_current_version(dataset_id)
        if current:
            current.is_current = False

        version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=next_number,
            is_current=True,
            created_by=owner_id,
            commit_message=commit_message,
            row_count=len(df),
            column_count=len(df.columns),
        )
        self.session.add(version)
        await self.session.flush()

        uploaded_file = UploadedFile(
            dataset_id=dataset_id,
            version_id=version.id,
            original_filename=safe_name,
            stored_filename=stored.stored_filename,
            file_size=len(data),
            checksum_sha256=checksum,
            mime_type=ext,
            file_extension=ext,
            storage_provider=stored.storage_provider,
            storage_path=stored.storage_path,
            uploaded_by=owner_id,
            upload_timestamp=datetime.now(timezone.utc),
        )
        self.session.add(uploaded_file)

        metadata = self._extract_metadata(dataset, version, df, len(data))
        self.session.add(metadata)

        quality = QualityEngine.analyze(df)
        report = ValidationReport(
            dataset_id=dataset_id,
            version_id=version.id,
            quality_score=quality["quality_score"],
            completeness_score=quality["completeness"],
            consistency_score=quality["consistency"],
            validity_score=quality["validity"],
            uniqueness_score=quality["uniqueness"],
            accuracy_score=quality["accuracy"],
            issues=quality["issues"],
            column_summary=quality["column_summary"],
        )
        self.session.add(report)

        dataset.current_version_id = version.id
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.quality_score = quality["quality_score"]
        dataset.total_size_bytes += len(data)
        version.quality_score = quality["quality_score"]
        version.validation_report_id = report.id
        await self.session.flush()
        logger.info("Version %d added to dataset %s", next_number, dataset_id)
        return version