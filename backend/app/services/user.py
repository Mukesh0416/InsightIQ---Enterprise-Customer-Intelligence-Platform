"""User management service implementing user CRUD and lifecycle logic."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.security.password import PasswordManager

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
        timezone: str = "UTC",
        language: str = "en",
        role_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> User:
        """Create a new user with hashed password."""
        existing = await self.user_repo.find_by_email(email)
        if existing:
            raise ConflictError(f"User with email {email} already exists.")
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            timezone=timezone,
            language=language,
            password_hash=PasswordManager.hash_password(password),
            role_id=role_id,
            organization_id=organization_id,
        )
        created = await self.user_repo.create(user)
        logger.info("User created: %s", email, extra={"extra_fields": {"user_id": str(created.id)}})
        return created

    async def get_user(self, user_id: UUID) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    async def update_user(self, user_id: UUID, **updates: object) -> User:
        user = await self.get_user(user_id)
        allowed = {"first_name", "last_name", "phone", "timezone", "language", "profile_image_url", "role_id", "organization_id"}
        for field, value in updates.items():
            if field in allowed and value is not None:
                setattr(user, field, value)
        await self.session.flush()
        return user

    async def deactivate_user(self, user_id: UUID) -> User:
        user = await self.get_user(user_id)
        user.is_active = False
        await self.session.flush()
        logger.info("User deactivated: %s", user_id)
        return user

    async def activate_user(self, user_id: UUID) -> User:
        user = await self.get_user(user_id)
        user.is_active = True
        await self.session.flush()
        logger.info("User activated: %s", user_id)
        return user

    async def soft_delete_user(self, user_id: UUID) -> None:
        user = await self.get_user(user_id)
        user.is_active = False
        await self.session.flush()
        logger.info("User soft-deleted: %s", user_id)

    async def list_users(
        self,
        query: str | None = None,
        is_active: bool | None = None,
        organization_id: UUID | None = None,
        role_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        skip = (page - 1) * page_size
        users = await self.user_repo.search(query, is_active, organization_id, role_id, skip, page_size)
        total = await self.user_repo.count_filtered(query, is_active, organization_id, role_id)
        return users, total