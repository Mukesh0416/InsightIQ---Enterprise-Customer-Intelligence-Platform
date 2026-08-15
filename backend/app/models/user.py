"""
User model for the InsightIQ domain.

Represents a registered user with profile information, authentication
state, and account status fields.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.types import UUID
from app.models.base import BaseModel


class User(BaseModel):
    """Registered user account with profile and authentication state."""

    __tablename__ = "users"

    # ── Identity ───────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
        comment="Verified email address used as the primary login identifier.",
    )
    first_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="User's given name.",
    )
    last_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="User's family name.",
    )

    # ── Authentication ─────────────────────────────────────────────────────
    password_hash: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Bcrypt/Argon2 hash of the user's password.",
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the last password change (null if never changed).",
    )
    password_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-serialized list of recent password hashes for history enforcement.",
    )

    # ── Account Status ─────────────────────────────────────────────────────
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user's email address has been verified.",
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the email was verified.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft-delete / active status flag.",
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Account lockout status due to failed login attempts.",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp until which the account is locked (null if not locked).",
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Consecutive failed login attempts since last successful login.",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the last successful login.",
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the last successful login (supports IPv6).",
    )

    # ── Profile ────────────────────────────────────────────────────────────
    phone: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="Contact phone number (E.164 format recommended).",
    )
    profile_image_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="URL to the user's profile image/avatar.",
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        default="UTC",
        nullable=False,
        comment="IANA timezone identifier (e.g. 'America/New_York').",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
        comment="ISO 639-1 language code (e.g. 'en', 'es').",
    )

    # ── Organization Relationship ──────────────────────────────────────────
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to the user's primary organization.",
    )
    organization = relationship(
        "Organization",
        back_populates="members",
        foreign_keys=[organization_id],
    )

    # ── Role Relationship ──────────────────────────────────────────────────
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to the user's assigned role.",
    )
    role = relationship("Role", back_populates="users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"