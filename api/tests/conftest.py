"""
Pytest configuration and shared fixtures.

This file contains:
- Database fixtures (test DB setup/teardown)
- API client fixtures (httpx.AsyncClient)
- Test data factories
- Mock configurations
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import get_db

# Test database URL (uses separate test database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/stock_ai_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for testing API endpoints.

    Usage:
        async def test_health(client):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """
    Database session for integration tests.

    Each test gets a fresh transaction that is rolled back after the test.
    This ensures tests are isolated and don't affect each other.
    """
    # TODO: Implement database fixture with transaction rollback
    # For now, this is a placeholder
    pass


# Test markers for organizing test runs
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
