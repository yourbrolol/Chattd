import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.chat.models import Base
from app.chat.schemas.auth import UserCreate, UserLogin
from app.chat.services.auth import register_user, login_user


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_register_and_login_user(session: AsyncSession) -> None:
    user, code = await register_user(session, UserCreate(username="alice", password="secret"))

    assert code == "ok"
    assert user is not None
    assert user.username == "alice"

    token_payload, login_code = await login_user(session, UserLogin(username="alice", password="secret"))

    assert login_code == "ok"
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]


@pytest.mark.anyio
async def test_register_rejects_duplicate_username(session: AsyncSession) -> None:
    await register_user(session, UserCreate(username="alice", password="secret"))
    user, code = await register_user(session, UserCreate(username="alice", password="another"))

    assert user is None
    assert code == "username_taken"
