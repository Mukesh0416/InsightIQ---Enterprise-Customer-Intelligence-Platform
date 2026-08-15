"""Organization management service."""

from __future__ import annotations

import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.repositories.user import UserRepository
from app.security.tokens import SecureTokenGenerator

logger = logging.getLogger(__name__)


class OrganizationService:
    """Business logic for organization management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def create_organization(self, name: str, owner_id: UUID, description: str | None = None) -> Organization:
        """Create a new organization with the given user as owner."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        org = Organization(name=name, slug=slug, description=description, owner_id=owner_id, is_active=True)
        self.session.add(org)
        await self.session.flush()
        member = OrganizationMember(organization_id=org.id, user_id=owner_id, role="owner")
        self.session.add(member)
        user = await self.session.get(User, owner_id)
        if user:
            user.organization_id = org.id
        await self.session.flush()
        logger.info("Organization created: %s", name, extra={"extra_fields": {"org_id": str(org.id)}})
        return org

    async def get_organization(self, org_id: UUID) -> Organization:
        org = await self.session.get(Organization, org_id)
        if not org:
            raise NotFoundError(f"Organization {org_id} not found.")
        return org

    async def update_organization(self, org_id: UUID, name: str | None = None, description: str | None = None) -> Organization:
        org = await self.get_organization(org_id)
        if name is not None:
            org.name = name
            org.slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if description is not None:
            org.description = description
        await self.session.flush()
        return org

    async def delete_organization(self, org_id: UUID) -> None:
        org = await self.get_organization(org_id)
        org.is_active = False
        await self.session.flush()
        logger.info("Organization soft-deleted: %s", org_id)

    async def list_organizations(self, page: int = 1, page_size: int = 20) -> tuple[list[Organization], int]:
        from sqlalchemy import func
        skip = (page - 1) * page_size
        stmt = select(Organization).where(Organization.is_active.is_(True)).offset(skip).limit(page_size)
        result = await self.session.execute(stmt)
        orgs = list(result.scalars().all())
        count_stmt = select(func.count(Organization.id)).where(Organization.is_active.is_(True))
        total = (await self.session.execute(count_stmt)).scalar_one()
        return orgs, total

    async def list_members(self, org_id: UUID) -> list[OrganizationMember]:
        await self.get_organization(org_id)
        stmt = select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def remove_member(self, org_id: UUID, member_id: UUID) -> None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == member_id,
        )
        result = await self.session.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Member not found in this organization.")
        if member.role == "owner":
            raise ValidationError("Cannot remove the organization owner.")
        await self.session.delete(member)
        await self.session.flush()
        logger.info("Member removed: org=%s user=%s", org_id, member_id)

    async def transfer_ownership(self, org_id: UUID, current_owner_id: UUID, new_owner_id: UUID) -> Organization:
        org = await self.get_organization(org_id)
        if org.owner_id != current_owner_id:
            raise ValidationError("Only the current owner can transfer ownership.")
        org.owner_id = new_owner_id
        await self.session.flush()
        logger.info("Ownership transferred: org=%s new_owner=%s", org_id, new_owner_id)
        return org