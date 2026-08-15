"""
Base model mixins and common column definitions for SQLAlchemy ORM models.

Provides reusable components that all domain models can inherit from,
including UUID primary keys, timestamp columns, and soft-delete support.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.types import UUID

from app.database.base import Base, TimestampMixin, utcnow


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with UUID primary key and timestamp columns.

    All domain models should inherit from this class to ensure a
    consistent primary key strategy and auditing columns.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Universal unique identifier for this record.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft-delete flag; inactive records are treated as deleted.",
    )

    def __repr__(self) -> str:
        """Return a human-readable representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"