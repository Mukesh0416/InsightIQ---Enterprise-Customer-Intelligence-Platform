"""RBAC service for role and permission management."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.role import Permission, Role, RolePermission
from app.models.user import User

logger = logging.getLogger(__name__)

DEFAULT_PERMISSIONS = {
    "user.read": ("View Users", "user", "read"),
    "user.write": ("Create/Update Users", "user", "write"),
    "user.delete": ("Delete Users", "user", "delete"),
    "dataset.upload": ("Upload Datasets", "dataset", "upload"),
    "dataset.delete": ("Delete Datasets", "dataset", "delete"),
    "analytics.run": ("Run Analytics", "analytics", "run"),
    "analytics.view": ("View Analytics", "analytics", "view"),
    "reports.download": ("Download Reports", "reports", "download"),
    "organization.manage": ("Manage Organization", "organization", "manage"),
    "settings.update": ("Update Settings", "settings", "update"),
}

DEFAULT_ROLES: dict[str, dict] = {
    "super_admin": {
        "description": "Full platform access with all permissions.",
        "hierarchy_level": 100,
        "permissions": list(DEFAULT_PERMISSIONS.keys()),
    },
    "organization_admin": {
        "description": "Administrative access for a single organization.",
        "hierarchy_level": 80,
        "permissions": [
            "user.read", "user.write", "user.delete",
            "dataset.upload", "dataset.delete",
            "analytics.run", "analytics.view",
            "reports.download", "organization.manage", "settings.update",
        ],
    },
    "manager": {
        "description": "Can manage datasets and run analytics.",
        "hierarchy_level": 60,
        "permissions": [
            "user.read", "dataset.upload", "dataset.delete",
            "analytics.run", "analytics.view", "reports.download",
        ],
    },
    "analyst": {
        "description": "Can run analytics and view reports.",
        "hierarchy_level": 40,
        "permissions": ["user.read", "analytics.run", "analytics.view", "reports.download"],
    },
    "viewer": {
        "description": "Read-only access to analytics and reports.",
        "hierarchy_level": 20,
        "permissions": ["analytics.view", "reports.download", "user.read"],
    },
}


class RBACService:
    """Business logic for role and permission management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def seed_default_roles_and_permissions(self) -> None:
        """Create default permissions and roles if they do not exist."""
        perm_map: dict[str, Permission] = {}
        for codename, (name, resource, action) in DEFAULT_PERMISSIONS.items():
            existing = await self._get_permission(codename)
            if existing:
                perm_map[codename] = existing
                continue
            perm = Permission(
                codename=codename, name=name, resource=resource, action=action
            )
            self.session.add(perm)
            perm_map[codename] = perm
        await self.session.flush()

        for role_name, config in DEFAULT_ROLES.items():
            existing_role = await self._get_role(role_name)
            if existing_role:
                continue
            role = Role(
                name=role_name,
                description=config["description"],
                is_system_role=True,
                hierarchy_level=config["hierarchy_level"],
            )
            self.session.add(role)
            await self.session.flush()
            for perm_codename in config["permissions"]:
                perm = perm_map[perm_codename]
                self.session.add(RolePermission(role_id=role.id, permission_id=perm.id))
        await self.session.flush()
        logger.info("Default roles and permissions seeded.")

    async def _get_permission(self, codename: str) -> Permission | None:
        result = await self.session.execute(
            select(Permission).where(Permission.codename == codename)
        )
        return result.scalar_one_or_none()

    async def _get_role(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_user_permissions(self, user_id: UUID) -> list[str]:
        user = await self.session.get(User, user_id)
        if not user or user.role is None:
            return []
        return [p.codename for p in user.role.permissions]

    async def get_role(self, role_id: UUID) -> Role:
        role = await self.session.get(Role, role_id)
        if not role:
            raise NotFoundError(f"Role {role_id} not found.")
        return role

    async def list_roles(self) -> list[Role]:
        result = await self.session.execute(select(Role).order_by(Role.hierarchy_level.desc()))
        return list(result.scalars().all())

    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(select(Permission).order_by(Permission.codename))
        return list(result.scalars().all())