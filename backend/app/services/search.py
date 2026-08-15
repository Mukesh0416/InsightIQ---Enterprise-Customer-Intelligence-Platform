"""
Search Engine.

Global search across datasets, users, organizations, predictions,
reports, notifications, and audit events with pagination and suggestions.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.services import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """Multi-entity search with ranking and suggestions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        query: str,
        organization_id: UUID | None = None,
        entity_types: list[str] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> SearchResponse:
        """
        Execute a global search across all entity types.

        Args:
            query: Search string.
            organization_id: Scope results to an organization.
            entity_types: Filter to specific entity types.
            skip: Pagination offset.
            limit: Max results.

        Returns:
            SearchResponse with ranked results and suggestions.
        """
        start = time.perf_counter()
        results: list[SearchResult] = []
        types = entity_types or ["dataset", "report", "notification", "audit", "user"]

        if "dataset" in types:
            results.extend(await self._search_datasets(query, organization_id))
        if "report" in types:
            results.extend(await self._search_reports(query, organization_id))
        if "notification" in types and organization_id:
            results.extend(await self._search_notifications(query, organization_id))
        if "audit" in types:
            results.extend(await self._search_audit(query, organization_id))
        if "user" in types:
            results.extend(await self._search_users(query, organization_id))

        # Simple relevance: exact matches first, then partial
        results.sort(key=lambda r: r.score, reverse=True)
        total = len(results)
        paginated = results[skip: skip + limit]
        suggestions = self._generate_suggestions(query, results)
        took_ms = round((time.perf_counter() - start) * 1000, 2)

        return SearchResponse(
            query=query,
            total=total,
            results=paginated,
            suggestions=suggestions,
            took_ms=took_ms,
        )

    async def _search_datasets(self, query: str, org_id: UUID | None) -> list[SearchResult]:
        from app.models.dataset import Dataset
        stmt = select(Dataset).where(
            Dataset.is_deleted.is_(False),
            or_(Dataset.name.ilike(f"%{query}%"), Dataset.description.ilike(f"%{query}%")),
        )
        if org_id:
            stmt = stmt.where(Dataset.organization_id == org_id)
        stmt = stmt.limit(10)
        result = await self.session.execute(stmt)
        return [
            SearchResult(
                entity_type="dataset",
                entity_id=str(d.id),
                title=d.name,
                description=d.description,
                score=1.0 if query.lower() in d.name.lower() else 0.6,
                metadata={"row_count": d.row_count, "quality_score": d.quality_score},
                created_at=d.created_at,
            )
            for d in result.scalars().all()
        ]

    async def _search_reports(self, query: str, org_id: UUID | None) -> list[SearchResult]:
        from app.models.services import Report
        stmt = select(Report).where(Report.name.ilike(f"%{query}%"))
        if org_id:
            stmt = stmt.where(Report.organization_id == org_id)
        stmt = stmt.limit(10)
        result = await self.session.execute(stmt)
        return [
            SearchResult(
                entity_type="report",
                entity_id=str(r.id),
                title=r.name,
                description=f"{r.report_type} report ({r.format})",
                score=1.0 if query.lower() in r.name.lower() else 0.5,
                metadata={"status": r.status, "format": r.format},
                created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]

    async def _search_notifications(self, query: str, org_id: UUID | None) -> list[SearchResult]:
        from app.models.services import Notification
        stmt = select(Notification).where(
            or_(Notification.title.ilike(f"%{query}%"), Notification.message.ilike(f"%{query}%"))
        )
        if org_id:
            stmt = stmt.where(Notification.organization_id == org_id)
        stmt = stmt.limit(5)
        result = await self.session.execute(stmt)
        return [
            SearchResult(
                entity_type="notification",
                entity_id=str(n.id),
                title=n.title,
                description=n.message[:120],
                score=0.4,
                metadata={"type": n.notification_type, "is_read": n.is_read},
                created_at=n.created_at,
            )
            for n in result.scalars().all()
        ]

    async def _search_audit(self, query: str, org_id: UUID | None) -> list[SearchResult]:
        from app.models.services import AuditEvent
        stmt = select(AuditEvent).where(
            or_(AuditEvent.event_type.ilike(f"%{query}%"), AuditEvent.resource_name.ilike(f"%{query}%"))
        )
        if org_id:
            stmt = stmt.where(AuditEvent.organization_id == org_id)
        stmt = stmt.limit(5)
        result = await self.session.execute(stmt)
        return [
            SearchResult(
                entity_type="audit",
                entity_id=str(a.id),
                title=a.event_type.replace(".", " ").title(),
                description=f"{a.action} on {a.resource_type}: {a.resource_name}",
                score=0.3,
                metadata={"category": a.event_category, "severity": a.severity},
                created_at=a.timestamp,
            )
            for a in result.scalars().all()
        ]

    async def _search_users(self, query: str, org_id: UUID | None) -> list[SearchResult]:
        from app.models.user import User
        stmt = select(User).where(
            User.is_active.is_(True),
            or_(
                User.email.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
            ),
        )
        if org_id:
            stmt = stmt.where(User.organization_id == org_id)
        stmt = stmt.limit(5)
        result = await self.session.execute(stmt)
        return [
            SearchResult(
                entity_type="user",
                entity_id=str(u.id),
                title=f"{u.first_name} {u.last_name}",
                description=u.email,
                score=1.0 if query.lower() in u.email.lower() else 0.7,
                created_at=u.created_at,
            )
            for u in result.scalars().all()
        ]

    @staticmethod
    def _generate_suggestions(query: str, results: list[SearchResult]) -> list[str]:
        """Generate search suggestions from result titles."""
        seen: set[str] = set()
        suggestions: list[str] = []
        for r in results[:5]:
            words = r.title.split()
            for word in words:
                if query.lower() in word.lower() and word not in seen and len(word) > 2:
                    suggestions.append(word)
                    seen.add(word)
        return suggestions[:5]
