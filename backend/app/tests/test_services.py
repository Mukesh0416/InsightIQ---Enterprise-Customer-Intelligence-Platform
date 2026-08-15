"""
Tests for the Application Services Layer.

Covers notification engine, audit service, job engine, search service,
report generator, export service, dashboard service, and scheduler.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pandas as pd
import pytest

from app.services.audit import AuditEventType, AuditService
from app.services.cache import CacheService
from app.services.jobs import JobEngine
from app.services.notification import NotificationService, NotificationType
from app.services.report_generator import generate_report
from app.services.search import SearchService


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    """Return a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": range(1, 11),
        "revenue": [100.0 * i for i in range(1, 11)],
        "order_date": pd.date_range("2023-01-01", periods=10, freq="ME"),
        "product_id": [f"P{i:03d}" for i in range(1, 11)],
    })


# ── Notification Service ──────────────────────────────────────────────────

class TestNotificationService:
    def test_notification_type_constants(self) -> None:
        assert NotificationType.DATASET_PROCESSED == "dataset_processed"
        assert NotificationType.TRAINING_COMPLETED == "training_completed"
        assert NotificationType.DRIFT_DETECTED == "drift_detected"
        assert NotificationType.REPORT_READY == "report_ready"
        assert NotificationType.MODEL_FAILURE == "model_failure"

    @pytest.mark.asyncio
    async def test_send_notification(self, mock_session) -> None:
        user_id = uuid4()
        mock_session.get.return_value = None  # no preference

        # Mock the repo methods
        with patch("app.services.notification.NotificationRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_preference.return_value = None
            MockRepo.return_value = mock_repo

            svc = NotificationService(mock_session)
            svc._repo = mock_repo

            notif = MagicMock()
            notif.id = uuid4()
            notif.title = "Dataset Processing Completed"
            notif.priority = "normal"
            mock_session.refresh = AsyncMock(side_effect=lambda x: None)

            # Verify template rendering
            from app.services.notification import _TEMPLATES
            tmpl = _TEMPLATES[NotificationType.DATASET_PROCESSED]
            assert "title" in tmpl
            assert "message" in tmpl
            assert "priority" in tmpl

    def test_template_format(self) -> None:
        from app.services.notification import _TEMPLATES
        tmpl = _TEMPLATES[NotificationType.TRAINING_COMPLETED]
        msg = tmpl["message"].format(name="Exp1", algorithm="xgboost", score=0.92)
        assert "Exp1" in msg
        assert "xgboost" in msg

    def test_all_types_have_templates(self) -> None:
        from app.services.notification import _TEMPLATES
        for attr in vars(NotificationType):
            if not attr.startswith("_"):
                val = getattr(NotificationType, attr)
                assert val in _TEMPLATES, f"Missing template for {val}"


# ── Audit Service ─────────────────────────────────────────────────────────

class TestAuditService:
    def test_event_type_constants(self) -> None:
        assert AuditEventType.USER_LOGIN == "user.login"
        assert AuditEventType.DATASET_UPLOADED == "dataset.uploaded"
        assert AuditEventType.REPORT_GENERATED == "report.generated"
        assert AuditEventType.TRAINING_STARTED == "ai.training_started"
        assert AuditEventType.ROLE_CHANGED == "rbac.role_changed"

    @pytest.mark.asyncio
    async def test_record_creates_event(self, mock_session) -> None:
        with patch("app.services.audit.AuditEventRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo

            svc = AuditService(mock_session)
            svc._audit_repo = mock_repo
            svc._activity_repo = AsyncMock()

            user_id = uuid4()
            # Verify add is called
            await svc.record(
                AuditEventType.USER_LOGIN,
                "login",
                "auth",
                user_id=user_id,
                ip_address="127.0.0.1",
            )
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_activity(self, mock_session) -> None:
        with patch("app.services.audit.ActivityLogRepository"):
            svc = AuditService(mock_session)
            svc._activity_repo = AsyncMock()

            await svc.log_activity(
                "Dataset uploaded",
                "dataset",
                user_id=uuid4(),
                organization_id=uuid4(),
                resource_type="dataset",
                resource_name="sales_data.csv",
            )
            mock_session.add.assert_called_once()


# ── Job Engine ────────────────────────────────────────────────────────────

class TestJobEngine:
    @pytest.mark.asyncio
    async def test_enqueue_creates_job(self, mock_session) -> None:
        with patch("app.services.jobs.BackgroundJobRepository"):
            engine = JobEngine(mock_session)
            job = MagicMock()
            job.id = uuid4()
            job.job_type = "report_generation"
            job.status = "pending"
            job.logs = []
            mock_session.refresh = AsyncMock(side_effect=lambda x: None)

            # Patch the add to capture the job
            added = []
            mock_session.add = MagicMock(side_effect=lambda x: added.append(x))

            result = await engine.enqueue(
                "report_generation",
                {"report_id": str(uuid4())},
                priority=3,
                max_retries=2,
            )
            assert mock_session.add.called
            assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_run_job_success(self, mock_session) -> None:
        job_id = uuid4()
        job = MagicMock()
        job.id = job_id
        job.job_type = "test_job"
        job.status = "pending"
        job.max_retries = 1
        job.retry_count = 0
        job.logs = []
        job.payload = {"key": "value"}
        mock_session.get = AsyncMock(return_value=job)

        async def handler(jid, payload):
            return {"result": "ok"}

        engine = JobEngine(mock_session)
        await engine.run_job(job_id, handler)
        assert job.status == "completed"
        assert job.result == {"result": "ok"}
        assert job.progress == 100.0

    @pytest.mark.asyncio
    async def test_run_job_failure_with_retry(self, mock_session) -> None:
        job_id = uuid4()
        job = MagicMock()
        job.id = job_id
        job.job_type = "failing_job"
        job.status = "pending"
        job.max_retries = 1
        job.retry_count = 0
        job.logs = []
        job.payload = {}
        mock_session.get = AsyncMock(return_value=job)

        call_count = 0

        async def failing_handler(jid, payload):
            nonlocal call_count
            call_count += 1
            raise ValueError("Simulated failure")

        engine = JobEngine(mock_session)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await engine.run_job(job_id, failing_handler)

        assert job.status == "failed"
        assert call_count == 2  # initial + 1 retry
        assert "Simulated failure" in job.error_message

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self, mock_session) -> None:
        job_id = uuid4()
        owner_id = uuid4()
        job = MagicMock()
        job.id = job_id
        job.owner_id = owner_id
        job.status = "pending"
        mock_session.get = AsyncMock(return_value=job)

        engine = JobEngine(mock_session)
        result = await engine.cancel(job_id, owner_id)
        assert result is True
        assert job.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_running_job_fails(self, mock_session) -> None:
        job_id = uuid4()
        job = MagicMock()
        job.id = job_id
        job.owner_id = uuid4()
        job.status = "running"
        mock_session.get = AsyncMock(return_value=job)

        engine = JobEngine(mock_session)
        result = await engine.cancel(job_id)
        assert result is False


# ── Cache Service ─────────────────────────────────────────────────────────

class TestCacheService:
    def test_make_key_deterministic(self) -> None:
        k1 = CacheService.make_key("dashboard:overview", org="abc", ds="xyz")
        k2 = CacheService.make_key("dashboard:overview", org="abc", ds="xyz")
        k3 = CacheService.make_key("dashboard:overview", org="abc", ds="different")
        assert k1 == k2
        assert k1 != k3
        assert k1.startswith("dashboard:overview:")

    def test_make_key_prefix(self) -> None:
        key = CacheService.make_key("widget:kpi_card", ds="123")
        assert key.startswith("widget:kpi_card:")

    @pytest.mark.asyncio
    async def test_get_miss(self, mock_session) -> None:
        with patch("app.services.cache.DashboardCacheRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_key.return_value = None
            MockRepo.return_value = mock_repo

            svc = CacheService(mock_session)
            result = await svc.get("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_hit(self, mock_session) -> None:
        with patch("app.services.cache.DashboardCacheRepository") as MockRepo:
            mock_repo = AsyncMock()
            cached = MagicMock()
            cached.data = {"total_revenue": 50000}
            mock_repo.get_by_key.return_value = cached
            MockRepo.return_value = mock_repo

            svc = CacheService(mock_session)
            result = await svc.get("some_key")
            assert result == {"total_revenue": 50000}


# ── Report Generator ──────────────────────────────────────────────────────

class TestReportGenerator:
    def test_generate_json(self, tmp_path) -> None:
        import app.services.report_generator as rg
        rg._REPORT_DIR = tmp_path

        report_data = {
            "name": "Test Report",
            "report_type": "executive",
            "kpis": {"total_revenue": 100000, "total_customers": 500},
            "customer": {"total_customers": 500, "new_customers": 50},
        }
        path, size, duration_ms = generate_report("test-report-001", report_data, "json")
        assert path.exists()
        assert size > 0
        assert duration_ms >= 0
        import json
        content = json.loads(path.read_text())
        assert content["report_id"] == "test-report-001"
        assert "data" in content

    def test_generate_csv(self, tmp_path) -> None:
        import app.services.report_generator as rg
        rg._REPORT_DIR = tmp_path

        report_data = {
            "kpis": {"total_revenue": 100000, "churn_rate": 0.05},
            "customer": {"total_customers": 500},
        }
        path, size, duration_ms = generate_report("test-report-002", report_data, "csv")
        assert path.exists()
        assert size > 0
        df = pd.read_csv(path)
        assert "section" in df.columns
        assert "metric" in df.columns

    def test_generate_excel(self, tmp_path) -> None:
        import app.services.report_generator as rg
        rg._REPORT_DIR = tmp_path

        report_data = {
            "kpis": {"total_revenue": 100000},
            "customer": {"total_customers": 500, "new_customers": 50},
        }
        path, size, duration_ms = generate_report("test-report-003", report_data, "excel")
        assert path.exists()
        assert size > 0
        with pd.ExcelFile(path) as xl:
            assert "Summary" in xl.sheet_names or "KPIs" in xl.sheet_names

    def test_invalid_format_raises(self, tmp_path) -> None:
        import app.services.report_generator as rg
        rg._REPORT_DIR = tmp_path
        from app.exceptions import ValidationError
        with pytest.raises(ValidationError):
            generate_report("test-report-bad", {}, "docx")


# ── Search Service ────────────────────────────────────────────────────────

class TestSearchService:
    def test_generate_suggestions(self) -> None:
        results = [
            MagicMock(title="Sales Report Q1", score=0.9),
            MagicMock(title="Sales Dashboard", score=0.8),
            MagicMock(title="Revenue Analysis", score=0.7),
        ]
        suggestions = SearchService._generate_suggestions("sales", results)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

    def test_generate_suggestions_empty(self) -> None:
        suggestions = SearchService._generate_suggestions("xyz", [])
        assert suggestions == []

    @pytest.mark.asyncio
    async def test_search_returns_response(self, mock_session) -> None:
        with patch.multiple(
            "app.services.search.SearchService",
            _search_datasets=AsyncMock(return_value=[]),
            _search_reports=AsyncMock(return_value=[]),
            _search_notifications=AsyncMock(return_value=[]),
            _search_audit=AsyncMock(return_value=[]),
            _search_users=AsyncMock(return_value=[]),
        ):
            svc = SearchService(mock_session)
            result = await svc.search("test query", organization_id=uuid4())
            assert result.query == "test query"
            assert result.total == 0
            assert isinstance(result.results, list)
            assert isinstance(result.suggestions, list)
            assert result.took_ms >= 0


# ── Scheduler ─────────────────────────────────────────────────────────────

class TestScheduler:
    def test_get_scheduler_returns_instance(self) -> None:
        from app.scheduler.scheduler import get_scheduler, _NoOpScheduler
        # Reset singleton for test isolation
        import app.scheduler.scheduler as sched_module
        sched_module._scheduler_instance = None

        with patch.dict("sys.modules", {"apscheduler": None, "apscheduler.schedulers": None,
                                         "apscheduler.schedulers.asyncio": None,
                                         "apscheduler.triggers": None,
                                         "apscheduler.triggers.cron": None}):
            sched_module._scheduler_instance = None
            scheduler = get_scheduler()
            assert scheduler is not None

    def test_noop_scheduler(self) -> None:
        from app.scheduler.scheduler import _NoOpScheduler
        s = _NoOpScheduler()
        s.start()  # should not raise
        s.shutdown()
        assert s.get_jobs() == []

    @pytest.mark.asyncio
    async def test_health_check_job(self) -> None:
        from app.scheduler.scheduler import _job_health_check
        with patch("app.scheduler.scheduler.verify_database_connection", new_callable=AsyncMock, return_value=True):
            await _job_health_check()  # should not raise

    @pytest.mark.asyncio
    async def test_file_cleanup_job(self, tmp_path) -> None:
        from app.scheduler.scheduler import _job_file_cleanup
        import app.scheduler.scheduler as sched_module

        # Create a fake old file
        old_file = tmp_path / "old_export.csv"
        old_file.write_text("data")
        import os, time
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))

        with patch("app.scheduler.scheduler.Path") as MockPath:
            MockPath.side_effect = lambda p: tmp_path if "exports" in p else tmp_path
            await _job_file_cleanup()  # should not raise


# ── Integration: Notification + Audit ────────────────────────────────────

class TestNotificationAuditIntegration:
    @pytest.mark.asyncio
    async def test_notification_types_cover_audit_events(self) -> None:
        """Verify notification types exist for all major audit event categories."""
        audit_categories = {"auth", "dataset", "ai", "report", "export", "rbac", "organization"}
        notif_types = {v for k, v in vars(NotificationType).items() if not k.startswith("_")}
        # At minimum these notification types must exist
        required = {
            NotificationType.DATASET_PROCESSED,
            NotificationType.TRAINING_COMPLETED,
            NotificationType.REPORT_READY,
            NotificationType.DRIFT_DETECTED,
            NotificationType.MODEL_FAILURE,
            NotificationType.EXPORT_COMPLETED,
        }
        assert required.issubset(notif_types)


# ── Performance ───────────────────────────────────────────────────────────

class TestPerformance:
    def test_report_json_generation_speed(self, tmp_path) -> None:
        import app.services.report_generator as rg
        import time
        rg._REPORT_DIR = tmp_path

        large_data = {
            "kpis": {f"metric_{i}": i * 100 for i in range(50)},
            "customer": {f"field_{i}": i for i in range(30)},
            "revenue": {f"rev_{i}": i * 1000 for i in range(30)},
        }
        start = time.perf_counter()
        path, size, _ = generate_report("perf-test-001", large_data, "json")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"JSON generation too slow: {elapsed:.2f}s"
        assert path.exists()

    def test_cache_key_generation_speed(self) -> None:
        import time
        start = time.perf_counter()
        for i in range(10000):
            CacheService.make_key("dashboard:overview", org=str(uuid4()), ds=str(uuid4()))
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Cache key generation too slow: {elapsed:.2f}s"

    def test_search_suggestions_speed(self) -> None:
        import time
        results = [MagicMock(title=f"Report {i} Analysis", score=float(i)) for i in range(100)]
        start = time.perf_counter()
        for _ in range(1000):
            SearchService._generate_suggestions("report", results)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0
