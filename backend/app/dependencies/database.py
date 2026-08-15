"""
Database session dependency for FastAPI route handlers.

Provides a convenience wrapper around the core ``get_async_session``
generator from the database layer.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Wraps ``app.database.session.get_async_session`` for convenience
    and re-export from the ``dependencies`` package.

    Usage:
        @router.get("/items")
        async def list_items(
            session: AsyncSession = Depends(get_db_session),
        ):
            ...
    """
    async for session in get_async_session():
        yield session