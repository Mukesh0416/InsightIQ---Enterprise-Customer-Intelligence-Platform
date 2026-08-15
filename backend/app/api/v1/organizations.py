"""Organization management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_permission
from app.dependencies.database import get_db_session
from app.models.organization import OrganizationMember
from app.models.user import User
from app.schemas.organization import (
    AcceptInvitationRequest, InviteMemberRequest, MemberResponse,
    OrganizationCreateRequest, OrganizationListResponse, OrganizationReadResponse,
    OrganizationUpdateRequest,
)
from app.services.organization import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def to_org_response(org) -> OrganizationReadResponse:
    return OrganizationReadResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        owner_id=org.owner_id,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("organization.manage")),
):
    service = OrganizationService(session)
    orgs, total = await service.list_organizations(page, page_size)
    return OrganizationListResponse(
        items=[to_org_response(o) for o in orgs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{org_id}", response_model=OrganizationReadResponse)
async def get_organization(
    org_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("organization.manage")),
):
    service = OrganizationService(session)
    org = await service.get_organization(org_id)
    return to_org_response(org)


@router.post("", response_model=OrganizationReadResponse, status_code=201)
async def create_organization(
    body: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    org = await service.create_organization(body.name, current_user.id, body.description)
    return to_org_response(org)


@router.put("/{org_id}", response_model=OrganizationReadResponse)
@router.patch("/{org_id}", response_model=OrganizationReadResponse)
async def update_organization(
    org_id: UUID,
    body: OrganizationUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("organization.manage")),
):
    service = OrganizationService(session)
    org = await service.update_organization(org_id, body.name, body.description)
    return to_org_response(org)


@router.delete("/{org_id}", status_code=204, response_class=Response)
async def delete_organization(
    org_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("organization.manage")),
) -> Response:
    service = OrganizationService(session)
    await service.delete_organization(org_id)
    return Response(status_code=204)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def list_members(
    org_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("user.read")),
):
    service = OrganizationService(session)
    members: list[OrganizationMember] = await service.list_members(org_id)
    result = []
    for m in members:
        user = await session.get(User, m.user_id)
        result.append(
            MemberResponse(
                id=m.id,
                user_id=m.user_id,
                email=user.email if user else "",
                first_name=user.first_name if user else "",
                last_name=user.last_name if user else "",
                role=m.role,
                joined_at=m.joined_at,
            )
        )
    return result


@router.delete("/{org_id}/members/{member_id}", status_code=204, response_class=Response)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("organization.manage")),
) -> Response:
    service = OrganizationService(session)
    await service.remove_member(org_id, member_id)
    return Response(status_code=204)


@router.post("/{org_id}/invite", status_code=201)
async def invite_member(
    org_id: UUID,
    body: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    from app.security.tokens import SecureTokenGenerator
    from app.config import settings
    from app.models.invitation import Invitation
    raw_token = SecureTokenGenerator.generate_token()
    inv = Invitation(
        email=body.email,
        organization_id=org_id,
        invited_by_id=current_user.id,
        token_hash=SecureTokenGenerator.hash_token(raw_token),
        expires_at=SecureTokenGenerator.generate_expires_at(days=settings.INVITATION_TOKEN_EXPIRE_DAYS),
        message=body.message,
    )
    session.add(inv)
    await session.flush()
    return {"message": "Invitation sent.", "token": raw_token}