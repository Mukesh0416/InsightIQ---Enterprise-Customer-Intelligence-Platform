"""
Notifications API endpoints.

GET    /notifications
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
DELETE /notifications/{id}
GET    /notifications/preferences
PATCH  /notifications/preferences
GET    /notifications/unread-count
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import NotificationPreferenceUpdate, NotificationResponse
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", summary="List notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    items, total = await svc.list_for_user(current_user.id, unread_only=unread_only, skip=skip, limit=limit)
    unread = await svc.unread_count(current_user.id)
    return {
        "items": [NotificationResponse.model_validate(n) for n in items],
        "total": total,
        "unread_count": unread,
        "skip": skip,
        "limit": limit,
    }


@router.get("/unread-count", summary="Unread notification count")
async def unread_count(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    return {"unread_count": await svc.unread_count(current_user.id)}


@router.patch("/read-all", summary="Mark all notifications as read")
async def mark_all_read(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    count = await svc.mark_all_read(current_user.id)
    return {"marked_read": count}


@router.patch("/{notification_id}/read", summary="Mark notification as read")
async def mark_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    await svc.mark_read(notification_id, current_user.id)
    return {"status": "read"}


@router.delete("/{notification_id}", status_code=204, response_class=Response, summary="Delete notification")
async def delete_notification(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    svc = NotificationService(session)
    await svc.delete(notification_id, current_user.id)
    return Response(status_code=204)


@router.get("/preferences", summary="Get notification preferences")
async def get_preferences(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    pref = await svc.get_or_create_preference(current_user.id)
    return {
        "email_enabled": pref.email_enabled,
        "in_app_enabled": pref.in_app_enabled,
        "webhook_enabled": pref.webhook_enabled,
        "webhook_url": pref.webhook_url,
        "type_preferences": pref.type_preferences,
        "quiet_hours_start": pref.quiet_hours_start,
        "quiet_hours_end": pref.quiet_hours_end,
    }


@router.patch("/preferences", summary="Update notification preferences")
async def update_preferences(
    updates: NotificationPreferenceUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    svc = NotificationService(session)
    pref = await svc.update_preference(current_user.id, updates.model_dump(exclude_none=True))
    return {"status": "updated", "email_enabled": pref.email_enabled, "in_app_enabled": pref.in_app_enabled}
