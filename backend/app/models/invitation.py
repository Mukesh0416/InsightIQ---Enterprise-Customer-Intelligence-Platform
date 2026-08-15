"""
Invitation model for user onboarding via email invitations.

Tracks the lifecycle of organisation membership invitations including
token management, expiration, and acceptance status.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.types import UUID
from app.models.base import BaseModel


class Invitation(BaseModel):
    """Email invitation for a user to join an organisation."""

    __tablename__ = "invitations"

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
        comment="Email address of the invited person.",
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the organisation the invitation is for.",
    )
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the user who sent the invitation.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="SHA-256 hash of the invitation token (raw token never stored).",
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the role the invited user will be assigned.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp after which the invitation is no longer valid.",
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the invitation was accepted (null if pending).",
    )
    is_accepted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the invitation has been accepted.",
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional personal message included with the invitation.",
    )

    def __repr__(self) -> str:
        return f"<Invitation(email={self.email}, accepted={self.is_accepted})>"