"""
Dashboard Service & Widget Engine.

Aggregates data from all platform modules into dashboard-ready JSON.
Supports KPI cards, charts, tables, and all widget types with caching.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cache import CacheService

logger = logging.getLogger(__name__)

_CACHE_TTL = 300  # 5 minutes


class DashboardService:
    """Aggregates platform data into dashboard-ready JSON with caching."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._cache = CacheService(session)

    async def get_overview(
        self,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """Return the full executive dashboard overview."""
        key = CacheService.make_key("dashboard:overview", org=str(organization_id), ds=str(dataset_id))
        cached = await self._cache.get(key)
        if cached:
            return cached

        result: dict[str, Any] = {
            "organization_id": str(organization_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_summary": await self._dataset_summary(organization_id),
            "processing_status": await self._processing_status(organization_id),
            "recent_activity": await self._recent_activity(organization_id),
            "organization_summary": await self._org_summary(organization_id),
        }

        if dataset_id:
            result["kpis"] = await self._kpi_cards(dataset_id)
            result["customer_overview"] = await self._customer_overview(dataset_id)
            result["revenue_overview"] = await self._revenue_overview(dataset_id)
            result["sales_overview"] = await self._sales_overview(dataset_id)
            result["data_quality_summary"] = await self._data_quality_summary(dataset_id)
            result["ai_prediction_summary"] = await self._ai_summary(organization_id)

        await self._cache.set(key, result, "overview", _CACHE_TTL, organization_id, dataset_id)
        return result

    async def get_kpis(self, dataset_id: UUID, organization_id: UUID) -> dict[str, Any]:
        """Return KPI card data."""
        key = CacheService.make_key("dashboard:kpis", ds=str(dataset_id))
        cached = await self._cache.get(key)
        if cached:
            return cached
        result = await self._kpi_cards(dataset_id)
        await self._cache.set(key, result, "kpi_cards", _CACHE_TTL, organization_id, dataset_id)
        return result

    async def get_activity(self, organization_id: UUID, skip: int = 0, limit: int = 20) -> dict[str, Any]:
        """Return recent activity feed."""
        from app.repositories.services import ActivityLogRepository
        repo = ActivityLogRepository(self.session)
        items, total = await repo.list_for_org(organization_id, skip=skip, limit=limit)
        return {
            "total": total,
            "items": [
                {
                    "id": str(a.id),
                    "activity_type": a.activity_type,
                    "title": a.title,
                    "description": a.description,
                    "resource_type": a.resource_type,
                    "resource_name": a.resource_name,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in items
            ],
        }

    async def get_widget(self, widget_type: str, dataset_id: UUID, config: dict[str, Any]) -> dict[str, Any]:
        """Generate a single widget's data payload."""
        key = CacheService.make_key(f"widget:{widget_type}", ds=str(dataset_id), cfg=str(sorted(config.items())))
        cached = await self._cache.get(key)
        if cached:
            return cached

        result = await self._build_widget(widget_type, dataset_id, config)
        await self._cache.set(key, result, widget_type, _CACHE_TTL, dataset_id=dataset_id)
        return result

    async def _build_widget(self, widget_type: str, dataset_id: UUID, config: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the appropriate widget builder."""
        builders = {
            "kpi_card": self._widget_kpi_card,
            "line_chart": self._widget_time_series,
            "area_chart": self._widget_time_series,
            "bar_chart": self._widget_bar_chart,
            "pie_chart": self._widget_pie_chart,
            "table": self._widget_table,
            "heatmap": self._widget_heatmap,
            "scatter": self._widget_scatter,
            "box_plot": self._widget_box_plot,
            "treemap": self._widget_treemap,
            "waterfall": self._widget_waterfall,
            "funnel": self._widget_funnel,
            "radar": self._widget_radar,
            "correlation_matrix": self._widget_correlation_matrix,
        }
        builder = builders.get(widget_type)
        if not builder:
            return {"error": f"Unknown widget type: {widget_type}"}
        return await builder(dataset_id, config)

    # ── Private data collectors ───────────────────────────────────────────

    async def _kpi_cards(self, dataset_id: UUID) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            biz = BusinessAnalyticsService(self.session)
            kpis = await biz.kpis(dataset_id)
            return {
                "cards": [
                    {"label": "Total Revenue", "value": kpis.get("total_revenue"), "unit": "$", "icon": "dollar"},
                    {"label": "Total Customers", "value": kpis.get("total_customers"), "icon": "users"},
                    {"label": "Total Orders", "value": kpis.get("total_orders"), "icon": "shopping-cart"},
                    {"label": "Avg Order Value", "value": kpis.get("average_order_value"), "unit": "$", "icon": "trending-up"},
                    {"label": "Churn Rate", "value": kpis.get("churn_rate"), "unit": "%", "icon": "alert"},
                    {"label": "Retention Rate", "value": kpis.get("retention_rate"), "unit": "%", "icon": "heart"},
                    {"label": "Revenue Growth", "value": kpis.get("revenue_growth_pct"), "unit": "%", "icon": "arrow-up"},
                    {"label": "ARPU", "value": kpis.get("arpu"), "unit": "$", "icon": "user"},
                ],
                "dataset_id": str(dataset_id),
            }
        except Exception as exc:
            logger.warning("KPI collection failed: %s", exc)
            return {"cards": [], "error": str(exc)}

    async def _customer_overview(self, dataset_id: UUID) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            return await BusinessAnalyticsService(self.session).customer_overview(dataset_id)
        except Exception as exc:
            return {"error": str(exc)}

    async def _revenue_overview(self, dataset_id: UUID) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            return await BusinessAnalyticsService(self.session).revenue_analysis(dataset_id)
        except Exception as exc:
            return {"error": str(exc)}

    async def _sales_overview(self, dataset_id: UUID) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            return await BusinessAnalyticsService(self.session).sales_analysis(dataset_id)
        except Exception as exc:
            return {"error": str(exc)}

    async def _data_quality_summary(self, dataset_id: UUID) -> dict[str, Any]:
        try:
            from app.services.eda import EDAService
            quality = await EDAService(self.session).get_quality(dataset_id)
            return {
                "overall_score": quality.get("overall_score"),
                "completeness": quality.get("completeness_score"),
                "consistency": quality.get("consistency_score"),
                "validity": quality.get("validity_score"),
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _ai_summary(self, organization_id: UUID) -> dict[str, Any]:
        try:
            from app.repositories.ai import MLModelRepository
            repo = MLModelRepository(self.session)
            models = await repo.list_by_org(organization_id, limit=5)
            return {
                "total_models": len(models),
                "active_models": sum(1 for m in models if m.status == "active"),
                "recent_models": [
                    {"id": str(m.id), "name": m.name, "algorithm": m.algorithm, "status": m.status}
                    for m in models[:3]
                ],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _dataset_summary(self, organization_id: UUID) -> dict[str, Any]:
        try:
            from app.repositories.dataset import DatasetRepository
            repo = DatasetRepository(self.session)
            datasets, total = await repo.list_datasets(organization_id=organization_id, limit=5)
            return {
                "total_datasets": total,
                "recent_datasets": [
                    {"id": str(d.id), "name": d.name, "row_count": d.row_count, "quality_score": d.quality_score}
                    for d in datasets
                ],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _processing_status(self, organization_id: UUID) -> dict[str, Any]:
        try:
            from app.models.dataset import ProcessingJob
            stmt = select(
                ProcessingJob.status, func.count(ProcessingJob.id)
            ).group_by(ProcessingJob.status)
            result = await self.session.execute(stmt)
            return {"by_status": {row[0]: row[1] for row in result.all()}}
        except Exception as exc:
            return {"error": str(exc)}

    async def _recent_activity(self, organization_id: UUID) -> list[dict[str, Any]]:
        try:
            from app.repositories.services import ActivityLogRepository
            repo = ActivityLogRepository(self.session)
            items, _ = await repo.list_for_org(organization_id, limit=10)
            return [
                {"title": a.title, "type": a.activity_type, "timestamp": a.timestamp.isoformat()}
                for a in items
            ]
        except Exception:
            return []

    async def _org_summary(self, organization_id: UUID) -> dict[str, Any]:
        try:
            from app.models.organization import Organization, OrganizationMember
            org = await self.session.get(Organization, organization_id)
            member_count = (await self.session.execute(
                select(func.count(OrganizationMember.id)).where(
                    OrganizationMember.organization_id == organization_id
                )
            )).scalar_one()
            return {
                "name": org.name if org else None,
                "member_count": member_count,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # ── Widget builders ───────────────────────────────────────────────────

    async def _widget_kpi_card(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        return await self._kpi_cards(dataset_id)

    async def _widget_time_series(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            trends = await BusinessAnalyticsService(self.session).trends(dataset_id)
            series = trends.get("monthly_series", {})
            return {
                "type": config.get("chart_type", "line_chart"),
                "labels": list(series.keys()) if isinstance(series, dict) else [],
                "datasets": [{"label": "Revenue", "data": list(series.values()) if isinstance(series, dict) else []}],
                "x_axis": "Month",
                "y_axis": config.get("metric", "Revenue"),
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_bar_chart(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            sales = await BusinessAnalyticsService(self.session).sales_analysis(dataset_id)
            top_products = sales.get("top_products", [])
            return {
                "type": "bar_chart",
                "labels": [p.get("product_id", "") for p in top_products[:10]],
                "datasets": [{"label": "Revenue", "data": [p.get("revenue", 0) for p in top_products[:10]]}],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_pie_chart(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            rfm = await BusinessAnalyticsService(self.session).rfm_analysis(dataset_id)
            dist = rfm.get("segment_distribution", {})
            return {
                "type": "pie_chart",
                "labels": list(dist.keys()),
                "data": list(dist.values()),
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_table(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            sales = await BusinessAnalyticsService(self.session).sales_analysis(dataset_id)
            return {
                "type": "table",
                "columns": ["customer_id", "revenue", "orders"],
                "rows": sales.get("top_customers", [])[:20],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_heatmap(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.eda import EDAService
            corr = await EDAService(self.session).get_correlation(dataset_id)
            matrix = corr.get("pearson_matrix", {})
            return {"type": "heatmap", "matrix": matrix}
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_scatter(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        return {"type": "scatter", "x": [], "y": [], "note": "Provide x_column and y_column in config."}

    async def _widget_box_plot(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.eda import EDAService
            dist = await EDAService(self.session).get_distribution(dataset_id)
            return {"type": "box_plot", "distributions": dist}
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_treemap(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            rev = await BusinessAnalyticsService(self.session).revenue_analysis(dataset_id)
            by_product = rev.get("revenue_by_product", {})
            return {
                "type": "treemap",
                "data": [{"name": k, "value": v} for k, v in list(by_product.items())[:20]],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_waterfall(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            trends = await BusinessAnalyticsService(self.session).trends(dataset_id)
            mom = trends.get("month_over_month", {})
            return {
                "type": "waterfall",
                "categories": list(mom.keys())[:12],
                "values": list(mom.values())[:12],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_funnel(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.business import BusinessAnalyticsService
            customer = await BusinessAnalyticsService(self.session).customer_overview(dataset_id)
            return {
                "type": "funnel",
                "stages": [
                    {"label": "Total Customers", "value": customer.get("total_customers", 0)},
                    {"label": "Active Customers", "value": customer.get("active_customers", 0)},
                    {"label": "Returning Customers", "value": customer.get("returning_customers", 0)},
                ],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_radar(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.eda import EDAService
            quality = await EDAService(self.session).get_quality(dataset_id)
            return {
                "type": "radar",
                "labels": ["Completeness", "Consistency", "Validity", "Uniqueness", "Accuracy"],
                "data": [
                    quality.get("completeness_score", 0),
                    quality.get("consistency_score", 0),
                    quality.get("validity_score", 0),
                    quality.get("uniqueness_score", 0),
                    quality.get("accuracy_score", 0),
                ],
            }
        except Exception as exc:
            return {"error": str(exc)}

    async def _widget_correlation_matrix(self, dataset_id: UUID, config: dict) -> dict[str, Any]:
        try:
            from app.services.eda import EDAService
            corr = await EDAService(self.session).get_correlation(dataset_id)
            return {"type": "correlation_matrix", "matrix": corr.get("pearson_matrix", {})}
        except Exception as exc:
            return {"error": str(exc)}
