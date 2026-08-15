"""
Export Engine.

Handles asynchronous data exports in CSV, Excel, PDF, and JSON formats.
Supports streaming responses for large datasets.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.services import ExportJob
from app.repositories.services import ExportJobRepository
from app.schemas.services import ExportRequest
from app.services.audit import AuditEventType, AuditService
from app.services.notification import NotificationService, NotificationType

logger = logging.getLogger(__name__)

_EXPORT_DIR = Path("exports/generated")
_EXPORT_EXPIRY_HOURS = 24


class ExportService:
    """Manages data export jobs and file generation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = ExportJobRepository(session)
        self._audit = AuditService(session)
        self._notif = NotificationService(session)

    async def create_export(self, request: ExportRequest, owner_id: UUID) -> ExportJob:
        """Create an export job record."""
        job = ExportJob(
            export_type=request.export_type,
            format=request.format,
            status="pending",
            dataset_id=request.dataset_id,
            organization_id=request.organization_id,
            owner_id=owner_id,
            config=request.config,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=_EXPORT_EXPIRY_HOURS),
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        await self._audit.record(
            AuditEventType.EXPORT_REQUESTED, "create", "export",
            user_id=owner_id,
            organization_id=request.organization_id,
            resource_type="export",
            resource_id=str(job.id),
        )
        await self.session.commit()
        logger.info("Export job created: %s (%s/%s)", job.id, request.export_type, request.format)
        return job

    async def run_export_job(self, job_id: UUID) -> None:
        """Execute the export and persist the file."""
        job = await self.session.get(ExportJob, job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self.session.flush()

        try:
            df = await self._collect_dataframe(job)
            _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            path, size = self._write_file(str(job_id), df, job.format)

            job.status = "completed"
            job.file_path = str(path)
            job.file_size_bytes = size
            job.row_count = len(df)
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()

            if job.owner_id:
                await self._notif.send(
                    job.owner_id,
                    NotificationType.EXPORT_COMPLETED,
                    {"format": job.format},
                    organization_id=job.organization_id,
                    resource_type="export",
                    resource_id=str(job_id),
                )
                await self.session.commit()

            await self._audit.record(
                AuditEventType.EXPORT_COMPLETED, "complete", "export",
                user_id=job.owner_id,
                resource_type="export",
                resource_id=str(job_id),
            )
            await self.session.commit()
            logger.info("Export completed: %s (%d rows, %d bytes)", job_id, len(df), size)

        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.error("Export failed: %s — %s", job_id, exc)

    async def _collect_dataframe(self, job: ExportJob) -> pd.DataFrame:
        """Load data for the export based on export_type."""
        if job.dataset_id:
            from app.repositories.dataset import DatasetRepository
            from app.storage import get_storage_provider

            repo = DatasetRepository(self.session)
            storage = get_storage_provider()
            version = await repo.get_current_version(job.dataset_id)
            if version:
                file = await repo.get_file_by_version(version.id)
                if file:
                    data = await storage.read(file.storage_path)
                    if file.file_extension == ".csv":
                        return pd.read_csv(io.BytesIO(data))
                    return pd.read_excel(io.BytesIO(data))
        return pd.DataFrame({"message": ["No data available for export."]})

    @staticmethod
    def _write_file(job_id: str, df: pd.DataFrame, fmt: str) -> tuple[Path, int]:
        """Write DataFrame to file in the requested format."""
        ext_map = {"csv": "csv", "excel": "xlsx", "json": "json", "pdf": "pdf"}
        ext = ext_map.get(fmt, fmt)
        path = _EXPORT_DIR / f"{job_id}.{ext}"

        if fmt == "csv":
            df.to_csv(str(path), index=False)
        elif fmt == "excel":
            df.to_excel(str(path), index=False, engine="openpyxl")
        elif fmt == "json":
            path.write_text(df.to_json(orient="records", indent=2, date_format="iso"), encoding="utf-8")
        elif fmt == "pdf":
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                doc = SimpleDocTemplate(str(path), pagesize=A4)
                sample = df.head(500)
                table_data = [list(sample.columns)] + sample.astype(str).values.tolist()
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ]))
                doc.build([t])
            except ImportError:
                path = path.with_suffix(".csv")
                df.to_csv(str(path), index=False)
        else:
            df.to_csv(str(path), index=False)

        return path, path.stat().st_size

    async def get_export(self, job_id: UUID) -> ExportJob:
        job = await self.session.get(ExportJob, job_id)
        if not job:
            raise NotFoundError(f"Export job {job_id} not found.")
        return job

    async def download_export(self, job_id: UUID) -> FileResponse:
        job = await self.get_export(job_id)
        if job.status != "completed" or not job.file_path:
            raise ValidationError("Export is not ready for download.")
        path = Path(job.file_path)
        if not path.exists():
            raise NotFoundError("Export file not found.")
        media_types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
            "json": "application/json",
        }
        return FileResponse(
            path=str(path),
            media_type=media_types.get(job.format, "application/octet-stream"),
            filename=f"export_{job_id}.{job.format}",
        )

    async def stream_csv(self, df: pd.DataFrame) -> StreamingResponse:
        """Stream a DataFrame as CSV without writing to disk."""
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        content = buf.read()
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )
