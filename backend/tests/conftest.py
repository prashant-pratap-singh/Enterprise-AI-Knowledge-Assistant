"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client fixture for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
