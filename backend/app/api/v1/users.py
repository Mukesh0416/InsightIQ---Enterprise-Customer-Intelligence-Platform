"""User management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_permission
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.user import (
    UserCreateRequest, UserListResponse, UserReadResponse, UserUpdateRequest,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def to_user_response(user: User) -> UserReadResponse:
    return UserReadResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        profile_image_url=user.profile_image_url,
        timezone=user.timezone,
        language=user.language,
        is_email_verified=user.is_email_verified,
        is_active=user.is_active,
        is_locked=user.is_locked,
        last_login_at=user.last_login_at,
        organization_id=str(user.organization_id) if user.organization_id else None,
        role_id=str(user.role_id) if user.role_id else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str | None = Query(None),
    is_active: bool | None = Query(None),
    organization_id: UUID | None = Query(None),
    role_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.read")),
):
    service = UserService(session)
    users, total = await service.list_users(
        query, is_active, organization_id, role_id, page, page_size
    )
    return UserListResponse(
        items=[to_user_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{user_id}", response_model=UserReadResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.read")),
):
    service = UserService(session)
    user = await service.get_user(user_id)
    return to_user_response(user)


@router.post("", response_model=UserReadResponse, status_code=201)
async def create_user(
    body: UserCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.write")),
):
    service = UserService(session)
    role_id = UUID(body.role_id) if body.role_id else None
    org_id = UUID(body.organization_id) if body.organization_id else None
    user = await service.create_user(
        body.email, body.password, body.first_name, body.last_name,
        body.phone, body.timezone, body.language, role_id, org_id,
    )
    return to_user_response(user)


@router.put("/{user_id}", response_model=UserReadResponse)
@router.patch("/{user_id}", response_model=UserReadResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.write")),
):
    service = UserService(session)
    user = await service.update_user(
        user_id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        timezone=body.timezone,
        language=body.language,
        profile_image_url=body.profile_image_url,
    )
    return to_user_response(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.delete")),
):
    service = UserService(session)
    await service.soft_delete_user(user_id)
    return None