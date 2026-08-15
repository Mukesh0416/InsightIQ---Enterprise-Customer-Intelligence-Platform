"""
Caching abstraction layer.

Provides a unified cache interface backed by the DashboardCache table.
Designed so Redis can be swapped in without changing call sites.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.services import DashboardCacheRepository

logger = logging.getLogger(__name__)

_DEFAULT_TTL_SECONDS = 300  # 5 minutes


def _make_key(prefix: str, **kwargs: Any) -> str:
    """Build a deterministic cache key from a prefix and keyword arguments."""
    payload = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.md5(payload.encode()).hexdigest()[:12]
    return f"{prefix}:{digest}"


class CacheService:
    """
    Database-backed cache with TTL support.

    All methods are async and accept an SQLAlchemy session.
    Replace the implementation body to use Redis without touching callers.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = DashboardCacheRepository(session)

    async def get(self, key: str) -> dict[str, Any] | None:
        """Return cached data or None if missing/expired."""
        entry = await self._repo.get_by_key(key)
        if entry:
            logger.debug("Cache HIT: %s", key)
            return entry.data
        logger.debug("Cache MISS: %s", key)
        return None

    async def set(
        self,
        key: str,
        data: dict[str, Any],
        widget_type: str = "generic",
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        organization_id: UUID | None = None,
        dataset_id: UUID | None = None,
    ) -> None:
        """Store data in cache with a TTL."""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        await self._repo.set(key, data, widget_type, expires_at, organization_id, dataset_id)

    async def invalidate_dataset(self, dataset_id: UUID) -> None:
        """Invalidate all cache entries for a dataset."""
        await self._repo.invalidate_for_dataset(dataset_id)

    async def purge_expired(self) -> int:
        """Remove all expired cache entries. Returns count removed."""
        return await self._repo.purge_expired()

    @staticmethod
    def make_key(prefix: str, **kwargs: Any) -> str:
        return _make_key(prefix, **kwargs)
