import pytest
from sqlalchemy import select

from app.chat.models import User
from ..conftest import new_credentials


@pytest.mark.anyio
async def test_account_creation(async_client, endpoints):
    # Register
    u1 = new_credentials()
    r = await async_client.post(endpoints.api.auth.register, json=u1)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == u1['username']

    # Login
    r = await async_client.post(endpoints.api.auth.login, json=u1)
    assert r.status_code == 200
    token = r.json()
    assert token["token_type"] == "bearer"
    assert token["access_token"]


@pytest.mark.anyio
async def test_incorrect_credentials(async_client, endpoints):
    # Ensure user exists
    u = new_credentials()
    await async_client.post(endpoints.api.auth.register, json=u)

    # Wrong password
    r = await async_client.post(endpoints.api.auth.login, json={"username": u["username"], "password": "wrong"})
    assert r.status_code == 400
    assert "Invalid" in r.json().get("detail", "")

    # Nonexistent user should get same external response
    # Use a generated username that was not registered to emulate nonexistent user
    non = new_credentials()
    r2 = await async_client.post(endpoints.api.auth.login, json={"username": non["username"], "password": "whatever"})
    assert r2.status_code == 400
    assert r2.json().get("detail") == r.json().get("detail")


@pytest.mark.anyio
async def test_empty_credentials(async_client, endpoints):
    # Pydantic validation should reject empty values for registration/login
    c = new_credentials(credentials={'username': "", 'password': ""})
    r = await async_client.post(endpoints.api.auth.register, json=c)
    assert r.status_code == 422

    r = await async_client.post(endpoints.api.auth.login, json=c)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_case_sensitivity(async_client, endpoints):
    # Register lowercase-like username
    u = new_credentials()
    await async_client.post(endpoints.api.auth.register, json=u)

    # Different case should fail (alter the case of the username)
    alt = u["username"].capitalize()
    r = await async_client.post(endpoints.api.auth.login, json={"username": alt, "password": u["password"]})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_long_credentials(async_client, endpoints):
    c = new_credentials(credentials={'username': "u" * 21, 'password': None})
    r2 = await async_client.post(endpoints.api.auth.register, json=c)
    assert r2.status_code == 422


@pytest.mark.anyio
async def test_unicode_username(async_client, endpoints):
    c = new_credentials(credentials={'username': "用户", 'password': None})
    r = await async_client.post(endpoints.api.auth.register, json=c)
    assert r.status_code == 201


@pytest.mark.anyio
async def test_null_bytes_username(async_client, endpoints):
    u = new_credentials(credentails={'username': None, 'password': "pa\x00ss\u2603"})
    r = await async_client.post(endpoints.api.auth.register, json=u)
    assert r.status_code == 201

    r = await async_client.post(endpoints.api.auth.login, json=u)
    assert r.status_code == 200
    assert r.json().get("access_token")


@pytest.mark.anyio
async def test_repeated_failed_logins_and_login_after_deletion(async_client, db_session, endpoints):
    # Register
    u = new_credentials()
    await async_client.post(endpoints.api.auth.register, json=u)

    # Repeated failed logins
    for _ in range(5):
        r = await async_client.post(endpoints.api.auth.login, json={"username": u["username"], "password": "wrong"})
        assert r.status_code == 400


@pytest.mark.anyio
async def test_login_after_deletion(async_client, db_session, endpoints):
    # Register
    u = new_credentials()
    await async_client.post(endpoints.api.auth.register, json=u)

    # Delete user directly from DB
    async with db_session as session:
        stmt = select(User).where(User.username == u["username"])
        res = await session.execute(stmt)
        user = res.scalars().first()
        assert user is not None
        await session.delete(user)
        await session.commit()

    # Login after deletion should fail
    r = await async_client.post(endpoints.api.auth.login, json=u)
    assert r.status_code == 400


@pytest.mark.anyio
async def test_protected_missing_access_token(async_client, endpoints):
    # Register a user to query
    u = new_credentials()
    r = await async_client.post(endpoints.api.auth.register, json=u)
    assert r.status_code == 201
    uid = r.json()["id"]

    # Accessing protected endpoint without cookie should return 401
    r = await async_client.get(endpoints.api.users.user_detail.format(user_id=uid))
    assert r.status_code == 401
