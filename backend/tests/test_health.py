"""Tests for health and readiness probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test /health endpoint returns 200 and healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app_name" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test /health/ready endpoint returns 200 and ready status."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns welcome payload."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
