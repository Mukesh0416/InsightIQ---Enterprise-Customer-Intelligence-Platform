"""
API layer package for routers and request handling.

Organises endpoints by version (``v1``, future ``v2``, etc.) and provides
a factory function to register all routers on the FastAPI application.

Usage:
    from app.api import register_api_routers
    register_api_routers(app)
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1 import api_v1_router
from app.config import settings


def register_api_routers(app: FastAPI) -> None:
    """
    Register all API routers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.include_router(
        api_v1_router,
        prefix=settings.API_PREFIX,
    )


__all__ = [
    "register_api_routers",
]