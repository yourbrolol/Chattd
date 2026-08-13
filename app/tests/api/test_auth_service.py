import pytest
from sqlalchemy import select

from app.chat.models import User


@pytest.mark.anyio
async def test_register_and_login_via_api(async_client, endpoints):
    # Register
    r = await async_client.post(endpoints.api.register, json={"username": "alice", "password": "secret"})
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "alice"

    # Login
    r = await async_client.post(endpoints.api.login, json={"username": "alice", "password": "secret"})
    assert r.status_code == 200
    token = r.json()
    assert token["token_type"] == "bearer"
    assert token["access_token"]


@pytest.mark.anyio
async def test_wrong_password_and_nonexistent_username(async_client, endpoints):
    # Ensure user exists
    await async_client.post(endpoints.api.register, json={"username": "carol", "password": "s3cret"})

    # Wrong password
    r = await async_client.post(endpoints.api.login, json={"username": "carol", "password": "wrong"})
    assert r.status_code == 400
    assert "Invalid" in r.json().get("detail", "")

    # Nonexistent user should get same external response
    r2 = await async_client.post(endpoints.api.login, json={"username": "noone", "password": "whatever"})
    assert r2.status_code == 400
    assert r2.json().get("detail") == r.json().get("detail")


@pytest.mark.anyio
async def test_empty_username_password_validation(async_client, endpoints):
    # Pydantic validation should reject empty values for registration/login
    r = await async_client.post(endpoints.api.register, json={"username": "", "password": ""})
    assert r.status_code == 422

    r = await async_client.post(endpoints.api.login, json={"username": "", "password": ""})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_case_sensitivity_and_long_username(async_client, endpoints):
    # Register lowercase
    await async_client.post(endpoints.api.register, json={"username": "eve", "password": "pw"})

    # Different case should fail
    r = await async_client.post(endpoints.api.login, json={"username": "Eve", "password": "pw"})
    assert r.status_code == 400

    # Username too long (>20) rejected by validation
    long_user = "u" * 21
    r2 = await async_client.post(endpoints.api.register, json={"username": long_user, "password": "pw"})
    assert r2.status_code == 422


@pytest.mark.anyio
async def test_unicode_username_and_null_byte_password(async_client, endpoints):
    uname = "用户"
    pwd = "pa\x00ss\u2603"
    r = await async_client.post(endpoints.api.register, json={"username": uname, "password": pwd})
    assert r.status_code == 201

    r = await async_client.post(endpoints.api.login, json={"username": uname, "password": pwd})
    assert r.status_code == 200
    assert r.json().get("access_token")


@pytest.mark.anyio
async def test_repeated_failed_logins_and_login_after_deletion(async_client, db_session, endpoints):
    # Register
    await async_client.post(endpoints.api.register, json={"username": "dave", "password": "pw"})

    # Repeated failed logins
    for _ in range(5):
        r = await async_client.post(endpoints.api.login, json={"username": "dave", "password": "wrong"})
        assert r.status_code == 400

    # Delete user directly from DB
    async with db_session as session:
        stmt = select(User).where(User.username == "dave")
        res = await session.execute(stmt)
        user = res.scalars().first()
        assert user is not None
        await session.delete(user)
        await session.commit()

    # Login after deletion should fail
    r = await async_client.post(endpoints.api.login, json={"username": "dave", "password": "pw"})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_missing_access_token_cookie_blocks_user_endpoint(async_client, endpoints):
    # Register a user to query
    r = await async_client.post(endpoints.api.register, json={"username": "frank", "password": "pw"})
    assert r.status_code == 201
    uid = r.json()["id"]

    # Accessing protected endpoint without cookie should return 401
    r = await async_client.get(endpoints.api.user_detail.format(user_id=uid))
    assert r.status_code == 401
