"""
Pytest fixtures for the webhook service tests.
Sets up an isolated test database and FastAPI TestClient.
"""

import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Ensure the service directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override DATABASE_URL before importing app — use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


from main import app
from database import init_db, engine, Base


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create fresh tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def valid_transaction_payload() -> dict:
    """A valid transaction webhook payload for testing."""
    return {
        "transaction_id": "txn_test_001",
        "merchant_id": "merchant_test_001",
        "amount": 1500.00,
        "currency": "INR",
        "status": "success",
        "payment_method": "upi",
        "customer_email": "test@example.com",
        "metadata": {"order_id": "ord_123"},
    }
