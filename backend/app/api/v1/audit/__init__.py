"""Audit API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import ActivityLogResponse, AuditEventResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", summary="Search audit events")
async def search_audit(
    organization_id: UUID | None = Query(None),
    user_id: UUID | None = Query(None),
    event_category: str | None = Query(None),
    event_type: str | None = Query(None),
    resource_type: str | None = Query(None),
    severity: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("audit.view")),
) -> dict:
    svc = AuditService(session)
    events, total = await svc.search_events(
        organization_id=organization_id,
        user_id=user_id,
        event_category=event_category,
        event_type=event_type,
        resource_type=resource_type,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [AuditEventResponse.model_validate(e) for e in events],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activity", summary="Activity feed")
async def activity_feed(
    organization_id: UUID = Query(...),
    activity_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("audit.view")),
) -> dict:
    svc = AuditService(session)
    items, total = await svc.get_activity_feed(organization_id, activity_type=activity_type, skip=skip, limit=limit)
    return {
        "items": [ActivityLogResponse.model_validate(a) for a in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{event_id}", response_model=AuditEventResponse, summary="Get audit event by ID")
async def get_audit_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("audit.view")),
) -> AuditEventResponse:
    from app.exceptions import NotFoundError
    from app.models.services import AuditEvent
    event = await session.get(AuditEvent, event_id)
    if not event:
        raise NotFoundError(f"Audit event {event_id} not found.")
    return AuditEventResponse.model_validate(event)
