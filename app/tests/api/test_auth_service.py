import pytest
from sqlalchemy import select

from app.chat.models import User
from app.tests.conftest import Credentials, user_payload_factory


@pytest.mark.anyio
async def test_register_and_login(async_client, endpoints):
    """Register a new user and log in — verify 201 creation response and bearer token."""
    # Register
    u1 = Credentials().as_dict()
    r = await async_client.post(endpoints.REGISTER, json=u1)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == u1['username']

    # Login
    r = await async_client.post(endpoints.LOGIN, json=u1)
    assert r.status_code == 200
    token = r.json()
    assert token["token_type"] == "bearer"
    assert token["access_token"]


@pytest.mark.anyio
async def test_login_rejects_wrong_password(async_client, endpoints):
    """Login with wrong or missing credentials returns 400 with a consistent detail message."""
    # Ensure user exists
    u = Credentials().as_dict()
    await async_client.post(endpoints.REGISTER, json=u)

    # Wrong password (must satisfy min-length so it reaches credential check -> 400)
    r = await async_client.post(endpoints.LOGIN, json={"username": u["username"], "password": "wrong_password_123"})
    assert r.status_code == 400
    body = r.json()
    assert body.get("detail") == "invalid_credentials"
    assert "Invalid" in body.get("error", {}).get("message", "")

    # Nonexistent user should get same external response
    # Use a generated username that was not registered to emulate nonexistent user
    non = Credentials().as_dict()
    r2 = await async_client.post(endpoints.LOGIN, json={"username": non["username"], "password": "whatever_password_123"})
    assert r2.status_code == 400
    assert r2.json().get("detail") == r.json().get("detail")


@pytest.mark.anyio
async def test_auth_reject_empty_fields(async_client, endpoints):
    """Register and login requests with empty username/password return 422 validation error."""
    # Pydantic validation should reject empty values for registration/login
    c = user_payload_factory(username="", password="")
    r = await async_client.post(endpoints.REGISTER, json=c)
    assert r.status_code == 422

    r = await async_client.post(endpoints.LOGIN, json=c)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_login_is_case_sensitive(async_client, endpoints):
    """Login with wrong-cased username is rejected even if same letters."""
    # Register lowercase-like username
    u = Credentials(username="aaa").as_dict()
    await async_client.post(endpoints.REGISTER, json=u)

    # Different case should fail (alter the case of the username)
    alt = u["username"].capitalize()
    r = await async_client.post(endpoints.LOGIN, json={"username": alt, "password": u["password"]})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_register_rejects_long_username(async_client, endpoints):
    """Usernames exceeding max length (20) return 422 validation error."""
    c = Credentials(**{'username': "u" * 21, 'password': None}).as_dict()
    r2 = await async_client.post(endpoints.REGISTER, json=c)
    assert r2.status_code == 422


@pytest.mark.anyio
async def test_register_accepts_unicode(async_client, endpoints):
    """Registration with unicode usernames is accepted."""
    c = Credentials(**{'username': "用户测试", 'password': None}).as_dict()
    r = await async_client.post(endpoints.REGISTER, json=c)
    assert r.status_code == 201


@pytest.mark.anyio
async def test_login_rejects_special_password_chars(async_client, endpoints):
    """Passwords with null bytes and special unicode chars are rejected."""
    u = Credentials(**{'username': None, 'password': "pa\x00ss\u2603"}).as_dict()
    r = await async_client.post(endpoints.REGISTER, json=u)
    assert r.status_code == 422

    r = await async_client.post(endpoints.LOGIN, json=u)
    assert r.status_code == 422
    assert r.json().get("access_token") is None


@pytest.mark.anyio
async def test_repeated_bad_logins(async_client, db_session, endpoints):
    """Repeated login attempts with wrong password all return 400."""
    # Register
    u = Credentials().as_dict()
    await async_client.post(endpoints.REGISTER, json=u)

    # Repeated failed logins (valid-length wrong password -> 400 each time)
    for _ in range(5):
        r = await async_client.post(endpoints.LOGIN, json={"username": u["username"], "password": "wrong_password_123"})
        assert r.status_code == 400


@pytest.mark.anyio
async def test_login_fails_after_db_deletion(async_client, db_session, endpoints):
    """Login attempt for a user deleted from DB returns 400."""
    # Register
    u = Credentials().as_dict()
    await async_client.post(endpoints.REGISTER, json=u)

    # Delete user directly from DB
    async with db_session as session:
        stmt = select(User).where(User.username == u["username"])
        res = await session.execute(stmt)
        user = res.scalars().first()
        assert user is not None
        await session.delete(user)
        await session.commit()

    # Login after deletion should fail
    r = await async_client.post(endpoints.LOGIN, json=u)
    assert r.status_code == 400


@pytest.mark.anyio
async def test_protected_endpoint_requires_auth(async_client, endpoints):
    """Accessing a protected endpoint without a cookie returns 401."""
    # Register a user to query
    u = Credentials().as_dict()
    r = await async_client.post(endpoints.REGISTER, json=u)
    assert r.status_code == 201
    uid = r.json()["id"]

    # Accessing protected endpoint without cookie should return 401
    r = await async_client.get(endpoints.user_detail(uid))
    assert r.status_code == 401

