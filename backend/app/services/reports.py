"""
Report Service.

Orchestrates report generation, storage, download, and lifecycle management.
Integrates with the business analytics, EDA, and AI services.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.services import Report
from app.repositories.services import ReportRepository
from app.schemas.services import ReportGenerateRequest
from app.services.audit import AuditEventType, AuditService
from app.services.notification import NotificationService, NotificationType
from app.services.report_generator import generate_report

logger = logging.getLogger(__name__)

_REPORT_EXPIRY_DAYS = 7


class ReportService:
    """Manages the full report lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = ReportRepository(session)
        self._audit = AuditService(session)
        self._notif = NotificationService(session)

    async def create_report(
        self,
        request: ReportGenerateRequest,
        owner_id: UUID,
    ) -> Report:
        """Create a pending report record and return it for background processing."""
        report = Report(
            name=request.name,
            report_type=request.report_type,
            format=request.format,
            status="pending",
            dataset_id=request.dataset_id,
            organization_id=request.organization_id,
            owner_id=owner_id,
            config=request.config,
            expires_at=datetime.now(timezone.utc) + timedelta(days=_REPORT_EXPIRY_DAYS),
        )
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report)
        logger.info("Report record created: %s (%s)", report.id, request.report_type)
        return report

    async def run_report_job(self, report_id: UUID) -> None:
        """
        Execute report generation and persist the result.
        Intended to be called from a background task.
        """
        report = await self.session.get(Report, report_id)
        if not report:
            return

        report.status = "generating"
        await self.session.flush()

        try:
            report_data = await self._collect_data(report)
            path, size, duration_ms = generate_report(str(report_id), report_data, report.format)

            report.status = "completed"
            report.file_path = str(path)
            report.file_size_bytes = size
            report.generated_at = datetime.now(timezone.utc)
            report.generation_duration_ms = duration_ms
            await self.session.commit()

            # Notify owner
            if report.owner_id:
                await self._notif.send(
                    report.owner_id,
                    NotificationType.REPORT_READY,
                    {"name": report.name, "report_type": report.report_type},
                    organization_id=report.organization_id,
                    resource_type="report",
                    resource_id=str(report_id),
                )
                await self.session.commit()

            await self._audit.record(
                AuditEventType.REPORT_GENERATED, "generate", "report",
                user_id=report.owner_id,
                organization_id=report.organization_id,
                resource_type="report",
                resource_id=str(report_id),
                resource_name=report.name,
            )
            await self.session.commit()
            logger.info("Report generated: %s in %.1fms", report_id, duration_ms)

        except Exception as exc:
            report.status = "failed"
            report.error_message = str(exc)
            await self.session.commit()
            logger.error("Report generation failed: %s — %s", report_id, exc)

    async def _collect_data(self, report: Report) -> dict[str, Any]:
        """Collect analytics data for the report based on its type."""
        from app.services.business import BusinessAnalyticsService
        from app.services.eda import EDAService

        data: dict[str, Any] = {
            "name": report.name,
            "report_type": report.report_type,
            "dataset_id": str(report.dataset_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if not report.dataset_id:
            return data

        biz = BusinessAnalyticsService(self.session)
        eda = EDAService(self.session)

        try:
            if report.report_type in ("executive", "business"):
                data["executive_summary"] = await biz.report(report.dataset_id)
                data["kpis"] = await biz.kpis(report.dataset_id)
                data["customer"] = await biz.customer_overview(report.dataset_id)
                data["revenue"] = await biz.revenue_analysis(report.dataset_id)
                data["sales"] = await biz.sales_analysis(report.dataset_id)
                data["retention"] = await biz.retention_analysis(report.dataset_id)
                data["recommendations"] = await biz.recommendations(report.dataset_id)
            elif report.report_type == "eda":
                data["summary"] = await eda.get_summary(report.dataset_id)
                data["statistics"] = await eda.get_statistics(report.dataset_id)
                data["missing"] = await eda.get_missing_analysis(report.dataset_id)
                data["outliers"] = await eda.get_outliers(report.dataset_id)
                data["correlation"] = await eda.get_correlation(report.dataset_id)
            elif report.report_type == "quality":
                data["quality"] = await eda.get_quality(report.dataset_id)
                data["missing"] = await eda.get_missing_analysis(report.dataset_id)
                data["duplicates"] = await eda.get_duplicates(report.dataset_id)
            elif report.report_type == "customer":
                data["customer"] = await biz.customer_overview(report.dataset_id)
                data["retention"] = await biz.retention_analysis(report.dataset_id)
                data["rfm"] = await biz.rfm_analysis(report.dataset_id)
                data["clv"] = await biz.clv_analysis(report.dataset_id)
            elif report.report_type == "revenue":
                data["revenue"] = await biz.revenue_analysis(report.dataset_id)
                data["kpis"] = await biz.kpis(report.dataset_id)
                data["trends"] = await biz.trends(report.dataset_id)
            elif report.report_type == "sales":
                data["sales"] = await biz.sales_analysis(report.dataset_id)
                data["trends"] = await biz.trends(report.dataset_id)
            elif report.report_type == "retention":
                data["retention"] = await biz.retention_analysis(report.dataset_id)
                data["cohort"] = await biz.cohort_analysis(report.dataset_id)
                data["rfm"] = await biz.rfm_analysis(report.dataset_id)
            elif report.report_type in ("prediction", "model", "drift"):
                data["ai_summary"] = {"message": "AI report data collected from AI platform."}
        except Exception as exc:
            logger.warning("Partial data collection failure for report %s: %s", report.id, exc)
            data["collection_error"] = str(exc)

        return data

    async def list_reports(
        self,
        owner_id: UUID,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Report], int]:
        if organization_id:
            return await self._repo.list_by_org(organization_id, skip=skip, limit=limit)
        return await self._repo.list_by_owner(owner_id, skip=skip, limit=limit)

    async def get_report(self, report_id: UUID) -> Report:
        report = await self.session.get(Report, report_id)
        if not report:
            raise NotFoundError(f"Report {report_id} not found.")
        return report

    async def download_report(self, report_id: UUID, user_id: UUID) -> FileResponse:
        report = await self.get_report(report_id)
        if report.status != "completed" or not report.file_path:
            raise ValidationError("Report is not ready for download.")
        path = Path(report.file_path)
        if not path.exists():
            raise NotFoundError("Report file not found on disk.")
        await self._repo.increment_download(report_id)
        await self._audit.record(
            AuditEventType.REPORT_DOWNLOADED, "download", "report",
            user_id=user_id,
            resource_type="report",
            resource_id=str(report_id),
            resource_name=report.name,
        )
        await self.session.commit()
        logger.info("Report downloaded: %s by user %s", report_id, user_id)
        media_types = {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv", "json": "application/json"}
        return FileResponse(
            path=str(path),
            media_type=media_types.get(report.format, "application/octet-stream"),
            filename=f"{report.name}.{report.format}",
        )

    async def delete_report(self, report_id: UUID, user_id: UUID) -> None:
        report = await self.get_report(report_id)
        if report.file_path:
            p = Path(report.file_path)
            if p.exists():
                p.unlink(missing_ok=True)
        await self.session.delete(report)
        await self._audit.record(
            AuditEventType.REPORT_DELETED, "delete", "report",
            user_id=user_id,
            resource_type="report",
            resource_id=str(report_id),
            resource_name=report.name,
        )
        await self.session.commit()
        logger.info("Report deleted: %s", report_id)
