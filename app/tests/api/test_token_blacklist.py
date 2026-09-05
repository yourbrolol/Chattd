import pytest
from jose import jwt
from sqlalchemy import select
from starlette.authentication import UnauthenticatedUser

from app.chat.models import RevokedToken
from app.core.auth import ALGORITHM, SECRET_KEY, authenticate_token
from app.core.token_blacklist import is_revoked
from app.tests.conftest import Credentials


@pytest.mark.anyio
async def test_logout_blacklists_jwt(async_client, db_session, endpoints):
    """Logged-out JWT is blacklisted: row persisted and token no longer authenticates."""
    # Register + login
    creds = Credentials().as_dict()
    r = await async_client.post(endpoints.REGISTER, json=creds)
    assert r.status_code == 201
    r = await async_client.post(endpoints.LOGIN, json=creds)
    assert r.status_code == 200
    token = r.json()["access_token"]
    jti = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["jti"]
    async_client.cookies.set("access_token", token)

    async with db_session as session:
        # Token authenticates before logout ...
        user = await authenticate_token(token, session)
        assert not isinstance(user, UnauthenticatedUser)
        assert await is_revoked(session, jti) is False

        # ... logout persists the jti in revoked_tokens ...
        r = await async_client.post(endpoints.LOGOUT)
        assert r.status_code in (200, 303, 307)
        row = (await session.execute(select(RevokedToken).where(RevokedToken.jti == jti))).scalars().first()
        assert row is not None, "logout must persist the token jti in revoked_tokens"
        assert await is_revoked(session, jti) is True

        # ... and the same token no longer authenticates.
        user = await authenticate_token(token, session)
        assert isinstance(user, UnauthenticatedUser)
