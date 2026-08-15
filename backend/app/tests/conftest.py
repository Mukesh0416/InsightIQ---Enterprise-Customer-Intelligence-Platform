"""
Pytest fixtures and configuration for the InsightIQ test suite.

Provides reusable fixtures for the FastAPI test client, database
session mocking, and common test utilities.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.config import settings
from app.main import create_app


@pytest.fixture(name="app")
def app_fixture() -> FastAPI:
    """
    Return a fully configured FastAPI application instance for testing.

    The application is created fresh for each test to ensure isolation.
    """
    return create_app()


@pytest.fixture(name="client")
async def client_fixture(
    app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Return an async HTTP client configured to talk to the test app.

    Usage:
        async def test_health(client: AsyncClient):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
    """
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def test_settings() -> None:
    """Keep the test environment stable without overriding default config values."""
    original_database_echo = settings.DATABASE_ECHO

    settings.DATABASE_ECHO = False
    yield

    settings.DATABASE_ECHO = original_database_echo