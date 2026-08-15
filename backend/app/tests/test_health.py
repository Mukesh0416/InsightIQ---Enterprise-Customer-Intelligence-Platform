"""
Unit tests for the health-check endpoints.

Tests the ``/health``, ``/ready``, and ``/live`` endpoints for correct
response structure and status codes.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient) -> None:
    """The ``/health`` endpoint should return HTTP 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_structure(client: AsyncClient) -> None:
    """The ``/health`` response should contain the expected fields."""
    response = await client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["status"] in ("healthy", "degraded")
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_ready_endpoint_returns_200(client: AsyncClient) -> None:
    """The ``/ready`` endpoint should return HTTP 200."""
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ready_endpoint_structure(client: AsyncClient) -> None:
    """The ``/ready`` response should contain the expected fields."""
    response = await client.get("/api/v1/ready")
    data = response.json()

    assert "status" in data
    assert "dependencies" in data
    assert data["status"] in ("ready", "not_ready")
    assert "database" in data["dependencies"]


@pytest.mark.asyncio
async def test_live_endpoint_returns_200(client: AsyncClient) -> None:
    """The ``/live`` endpoint should return HTTP 200."""
    response = await client.get("/api/v1/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_live_endpoint_structure(client: AsyncClient) -> None:
    """The ``/live`` response should contain the expected fields."""
    response = await client.get("/api/v1/live")
    data = response.json()

    assert "status" in data
    assert data["status"] == "alive"