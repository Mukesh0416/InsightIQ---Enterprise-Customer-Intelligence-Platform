"""
Application entrypoint for the InsightIQ backend service.

Creates and configures the FastAPI application, registers middleware,
exception handlers, and API routers, and defines lifecycle event
handlers (startup / shutdown).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import register_api_routers
from app.config import (
    API_CONTACT,
    API_DESCRIPTION,
    API_LICENSE_INFO,
    API_TITLE,
    API_VERSION,
    TAGS_METADATA,
    settings,
)
from app.database.session import (
    async_session_factory,
    verify_database_connection,
)
from app.exceptions.handlers import register_exception_handlers
from app.logging import configure_logging
from app.middleware import configure_middleware
from app.services.rbac import RBACService
from app.scheduler import get_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle handler.

    Runs startup logic before yielding control to the application,
    then runs shutdown logic after the application stops.
    """
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.APP_ENV)

    # Verify database connectivity
    db_ok = await verify_database_connection()
    if db_ok:
        logger.info("Database connection verified successfully.")
        # Seed default roles and permissions
        try:
            async with async_session_factory() as session:
                rbac = RBACService(session)
                await rbac.seed_default_roles_and_permissions()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to seed RBAC roles: %s", exc)
    else:
        logger.warning(
            "Database connection failed. The application will start "
            "but database-dependent endpoints may not work."
        )

    # Start scheduler
    try:
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scheduler failed to start: %s", exc)

    yield  # Application runs here

    # ── Shutdown ───────────────────────────────────────────────────────────
    try:
        get_scheduler().shutdown(wait=False)
    except Exception:  # noqa: BLE001
        pass
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """
    Factory function that creates and configures the FastAPI application.

    Returns:
        A fully configured FastAPI application instance.
    """
    # ── Initialise logging ─────────────────────────────────────────────────
    configure_logging()

    # ── Create FastAPI app ─────────────────────────────────────────────────
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        contact=API_CONTACT,
        license_info=API_LICENSE_INFO,
        openapi_tags=TAGS_METADATA,
        docs_url=settings.API_DOCS_URL,
        redoc_url=settings.API_REDOC_URL,
        openapi_url=settings.API_OPENAPI_URL,
        lifespan=lifespan,
    )

    # ── Register middleware ────────────────────────────────────────────────
    configure_middleware(app)

    # ── Register exception handlers ───────────────────────────────────────
    register_exception_handlers(app)

    # ── Register API routers ───────────────────────────────────────────────
    register_api_routers(app)

    logger.info(
        "Application configured: docs=%s, redoc=%s, openapi=%s",
        settings.API_DOCS_URL,
        settings.API_REDOC_URL,
        settings.API_OPENAPI_URL,
    )

    return app


# Module-level application instance for ASGI servers (Uvicorn, etc.)
app = create_app()