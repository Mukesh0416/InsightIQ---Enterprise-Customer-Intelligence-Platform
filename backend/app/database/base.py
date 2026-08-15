"""
SQLAlchemy declarative base and mixins for all ORM models.

Provides the ``Base`` class that every model should inherit from, along
with common mixins (timestamp columns, primary key strategies) that can
be reused across the domain.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Declarative base for all InsightIQ ORM models.

    All database models should inherit from this class. It configures the
    naming convention for constraints and sets the default schema.
    """


# ── Naming convention for constraints ──────────────────────────────────────
# Applied to the Base metadata after class definition to avoid Pylance
# false positives with DeclarativeBase.metadata.
Base.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class TimestampMixin:
    """
    Mixin that adds ``created_at`` and ``updated_at`` timestamp columns.

    ``created_at`` defaults to ``now()`` and is set once on insert.
    ``updated_at`` is set on every insert and update via ``onupdate``.
    Both are stored as UTC-aware timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created (UTC).",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated (UTC).",
    )


def utcnow() -> datetime:
    """Return the current UTC datetime, safe for default factories."""
    return datetime.now(timezone.utc)