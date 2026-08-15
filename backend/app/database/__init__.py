"""
Database layer package for engine, session, and migration support.

Provides the declarative ``Base``, async engine, session factory, and
a FastAPI-compatible dependency for obtaining database sessions.

Usage:
    from app.database import Base, get_async_session
    from app.database.base import TimestampMixin
    from app.database.session import verify_database_connection
"""

from app.database.base import Base, TimestampMixin, utcnow
from app.database.session import (
    engine,
    async_session_factory,
    get_async_session,
    verify_database_connection,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "utcnow",
    "engine",
    "async_session_factory",
    "get_async_session",
    "verify_database_connection",
]