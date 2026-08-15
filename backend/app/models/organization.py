"""
Organization and OrganizationMember models for multi-tenant support.

Organisations group users and manage invitations. Ownership and member
roles are tracked via the OrganizationMember association model.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.types import UUID
from app.models.base import BaseModel


class Organization(BaseModel):
    """Tenant entity representing a customer organisation."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        nullable=False,
        index=True,
        comment="Display name of the organisation.",
    )
    slug: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-safe unique identifier derived from the name.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the organisation.",
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the user who owns this organisation.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the organisation is active (soft-delete).",
    )
    settings: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-serialized organisation settings.",
    )

    # Relationships
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        post_update=True,
    )
    members = relationship(
        "User",
        back_populates="organization",
        foreign_keys="User.organization_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Organization(name={self.name})>"


class OrganizationMember(BaseModel):
    """Association model tracking user membership within an organisation."""

    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_org_member",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        default="member",
        nullable=False,
        comment="Member role within the organisation ('owner', 'admin', 'member').",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when the user joined the organisation.",
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the user who sent the invitation.",
    )

    def __repr__(self) -> str:
        return f"<OrganizationMember(org={self.organization_id}, user={self.user_id})>"