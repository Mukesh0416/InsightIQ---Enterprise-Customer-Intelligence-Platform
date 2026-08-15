"""
Database engine, session factory, and session management.

Provides a configured SQLAlchemy ``AsyncEngine`` and ``async_sessionmaker``
for use throughout the application. Exposes a helper to verify database
connectivity and a dependency for FastAPI route handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
)

# ── Session factory ───────────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    Usage:
        @router.get("/items")
        async def list_items(
            session: AsyncSession = Depends(get_async_session),
        ):
            ...

    The session is automatically closed when the request finishes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def verify_database_connection() -> bool:
    """
    Check whether the database is reachable by executing a lightweight query.

    Returns ``True`` if the connection succeeds, ``False`` otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return True
    except Exception:  # noqa: BLE001
        return False