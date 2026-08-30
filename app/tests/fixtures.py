import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient

# Ensure default testing environment is set before importing any app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./app/tests/test_db.sqlite3?cache=shared")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("TESTING", "true")

from app.main import app
from app.core.database import init_db, close_db, SessionLocal, Base, engine

HOST = "http://127.0.0.1:8000/"

@pytest.fixture(scope="session", autouse=True)
def init_database():
    # The SQLite file persists between runs; drop old data to avoid
    # UNIQUE constraint collisions from previous sessions.
    asyncio.run(_reset_db())
    # Create DB tables once per test session
    asyncio.run(init_db())
    yield
    # We could drop them, but since it's in-memory cache=shared, it will clear when process exits


async def _reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def async_client():
    async with AsyncClient(base_url=HOST, transport=ASGITransport(app=app)) as ac:
        yield ac

@pytest.fixture
def sync_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session
