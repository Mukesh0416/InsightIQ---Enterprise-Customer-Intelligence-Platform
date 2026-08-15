"""Search API endpoint."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.services import SearchResponse
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Global search",
    description="Search across datasets, reports, notifications, audit events, and users.",
)
async def global_search(
    q: str = Query(..., min_length=1, max_length=256, description="Search query"),
    organization_id: UUID | None = Query(None),
    entity_types: str | None = Query(None, description="Comma-separated: dataset,report,notification,audit,user"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResponse:
    types = [t.strip() for t in entity_types.split(",")] if entity_types else None
    svc = SearchService(session)
    return await svc.search(q, organization_id=organization_id, entity_types=types, skip=skip, limit=limit)
