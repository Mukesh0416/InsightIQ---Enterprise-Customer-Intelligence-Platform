"""Dataset management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.dataset import (
    DatasetListResponse, DatasetMetadataResponse, DatasetPreviewResponse,
    DatasetReadResponse, DatasetVersionResponse, NewVersionRequest,
    UploadFileResponse, ValidationReportResponse,
)
from app.services.dataset import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def to_dataset_response(d) -> DatasetReadResponse:
    return DatasetReadResponse(
        id=d.id, name=d.name, description=d.description, owner_id=d.owner_id,
        organization_id=d.organization_id, current_version_id=d.current_version_id,
        is_deleted=d.is_deleted, row_count=d.row_count, column_count=d.column_count,
        quality_score=d.quality_score, total_size_bytes=d.total_size_bytes,
        created_at=d.created_at, updated_at=d.updated_at,
    )


def to_version_response(v) -> DatasetVersionResponse:
    return DatasetVersionResponse(
        id=v.id, dataset_id=v.dataset_id, version_number=v.version_number,
        is_current=v.is_current, created_by=v.created_by, commit_message=v.commit_message,
        row_count=v.row_count, column_count=v.column_count, quality_score=v.quality_score,
        created_at=v.created_at,
    )


@router.post("/upload", response_model=DatasetReadResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV, XLSX, or XLS file to upload."),
    name: str | None = Form(None, description="Optional dataset display name."),
    description: str | None = Form(None, description="Optional dataset description."),
    current_user: User = Depends(require_permission("dataset.upload")),
    session: AsyncSession = Depends(get_db_session),
):
    service = DatasetService(session)
    data = await file.read()
    dataset = await service.upload(
        file.filename or "upload.csv",
        data,
        current_user.id,
        current_user.organization_id,
        name,
        description,
    )
    return to_dataset_response(dataset)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Search by name or description."),
    current_user: User = Depends(require_permission("dataset.upload")),
    session: AsyncSession = Depends(get_db_session),
):
    service = DatasetService(session)
    datasets, total = await service.list_datasets(current_user.id, None, query, page, page_size)
    return DatasetListResponse(
        items=[to_dataset_response(d) for d in datasets],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{dataset_id}", response_model=DatasetReadResponse)
async def get_dataset_detail(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("dataset.upload")),
):
    service = DatasetService(session)
    dataset = await service.get_dataset(dataset_id)
    return to_dataset_response(dataset)


@router.delete("/{dataset_id}", status_code=204, response_class=Response)
async def delete_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("dataset.delete")),
) -> Response:
    service = DatasetService(session)
    await service.delete_dataset(dataset_id)
    return Response(status_code=204)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    service = DatasetService(session)
    data = await service.get_preview(dataset_id, limit)
    return data


@router.get("/{dataset_id}/metadata", response_model=DatasetMetadataResponse)
async def get_dataset_metadata(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("dataset.upload")),
):
    service = DatasetService(session)
    md = await service.get_metadata(dataset_id)
    return DatasetMetadataResponse(
        dataset_id=md.dataset_id, version_id=md.version_id, row_count=md.row_count,
        column_count=md.column_count, column_names=md.column_names or [],
        column_types=md.column_types or {}, null_counts=md.null_counts or {},
        distinct_counts=md.distinct_counts or {}, memory_usage_bytes=md.memory_usage_bytes,
        file_size=md.file_size, encoding=md.encoding, extracted_at=md.extracted_at,
    )


@router.get("/{dataset_id}/validation", response_model=ValidationReportResponse)
async def get_dataset_validation(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("analytics.view")),
):
    service = DatasetService(session)
    report = await service.get_validation(dataset_id)
    return ValidationReportResponse(
        dataset_id=report.dataset_id, version_id=report.version_id,
        quality_score=report.quality_score, completeness=report.completeness_score,
        consistency=report.consistency_score, validity=report.validity_score,
        uniqueness=report.uniqueness_score, accuracy=report.accuracy_score,
        issues=report.issues or [], column_summary=report.column_summary,
        is_valid=report.is_valid,
    )


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
async def list_versions(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("dataset.upload")),
):
    service = DatasetService(session)
    versions = await service.get_versions(dataset_id)
    return [to_version_response(v) for v in versions]


@router.post("/{dataset_id}/versions", response_model=DatasetVersionResponse, status_code=201)
async def add_version(
    dataset_id: UUID,
    file: UploadFile = File(..., description="New file for this version."),
    commit_message: str | None = Form(None, max_length=500),
    current_user: User = Depends(require_permission("dataset.upload")),
    session: AsyncSession = Depends(get_db_session),
):
    service = DatasetService(session)
    data = await file.read()
    version = await service.add_version(
        dataset_id, file.filename or "upload.csv", data, current_user.id, commit_message
    )
    return to_version_response(version)


@router.get("/download/{dataset_id}")
async def download_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("reports.download")),
):
    service = DatasetService(session)
    data, filename, mime = await service.download(dataset_id)
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )