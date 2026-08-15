"""
Role, Permission, and RolePermission models for RBAC.

Defines the core RBAC data model: permissions represent atomic actions,
roles group permissions, and users are assigned roles.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.types import UUID
from app.models.base import BaseModel


class Permission(BaseModel):
    """Atomic permission representing a specific action on a resource."""

    __tablename__ = "permissions"

    codename: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique permission identifier (e.g. 'user.read', 'dataset.upload').",
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Human-readable permission display name.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional detailed description of what this permission grants.",
    )
    resource: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="The resource type this permission applies to (e.g. 'user', 'dataset').",
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="The action this permission allows (e.g. 'read', 'write', 'delete').",
    )

    def __repr__(self) -> str:
        return f"<Permission(codename={self.codename})>"


class Role(BaseModel):
    """Named role that groups a set of permissions."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="Role display name (e.g. 'Admin', 'Analyst', 'Viewer').",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the role's purpose.",
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="System roles cannot be deleted or modified.",
    )
    hierarchy_level: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Numeric level for role hierarchy (higher = more privileged).",
    )

    # Relationships
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Role(name={self.name})>"


class RolePermission(BaseModel):
    """Many-to-many association between roles and permissions."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission",
        ),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<RolePermission(role={self.role_id}, perm={self.permission_id})>"


# Add back-populates to Permission
Permission.roles = relationship(
    "Role",
    secondary="role_permissions",
    back_populates="permissions",
    lazy="selectin",
)