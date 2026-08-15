"""User repository for database operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def find_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def find_active_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email, User.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str | None = None,
        is_active: bool | None = None,
        organization_id: UUID | None = None,
        role_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        stmt = select(User)
        if query:
            stmt = stmt.where(
                User.first_name.ilike(f"%{query}%")
                | User.last_name.ilike(f"%{query}%")
                | User.email.ilike(f"%{query}%")
            )
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if organization_id:
            stmt = stmt.where(User.organization_id == organization_id)
        if role_id:
            stmt = stmt.where(User.role_id == role_id)
        stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        query: str | None = None,
        is_active: bool | None = None,
        organization_id: UUID | None = None,
        role_id: UUID | None = None,
    ) -> int:
        from sqlalchemy import func
        stmt = select(func.count(User.id))
        if query:
            stmt = stmt.where(
                User.first_name.ilike(f"%{query}%")
                | User.last_name.ilike(f"%{query}%")
                | User.email.ilike(f"%{query}%")
            )
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if organization_id:
            stmt = stmt.where(User.organization_id == organization_id)
        if role_id:
            stmt = stmt.where(User.role_id == role_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()