"""
Cross-database compatible column types.

Provides a UUID type that works on both PostgreSQL and SQLite,
so the application can run without a PostgreSQL server during
local development.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Use SQLAlchemy's cross-database Uuid type (works on PostgreSQL, SQLite, etc.)
# This is available in SQLAlchemy 2.0+.
UUID = Uuid

__all__ = ["UUID", "PG_UUID"]