import pytest
from app.tests.fixtures import app

async def _async_login_and_set_cookie(client, username, password):
    from app.tests.conftest import ENDPOINTS
    await client.post(ENDPOINTS.api.auth.register, json={"username": username, "password": password})
    r = await client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


def _sync_login_and_set_cookie(client, username, password):
    from app.tests.conftest import ENDPOINTS
    client.post(ENDPOINTS.api.auth.register, json={"username": username, "password": password})
    r = client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


async def login_as(client, username, password):
    """Logs in an already registered user and sets cookie on client."""
    from app.tests.conftest import ENDPOINTS
    r = await client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


def login_as_sync(client, username, password):
    """Sync version of login_as."""
    from app.tests.conftest import ENDPOINTS
    r = client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


async def authenticated_client_for(client, username, password):
    """Registers, logs in a user, and returns client with authenticated cookie."""
    await _async_login_and_set_cookie(client, username, password)
    return client


def authenticated_client_for_sync(client, username, password):
    """Sync version of authenticated_client_for."""
    _sync_login_and_set_cookie(client, username, password)
    return client




def create_room_sync(client, endpoints, room_name, room_type):
    return client.post(endpoints.api.rooms.room_create.rstrip('/'), json={"room_name": room_name, "room_type": room_type})


async def create_room_async(client, endpoints, room_name, room_type):
    return await client.post(endpoints.api.rooms.room_create.rstrip('/'), json={"room_name": room_name, "room_type": room_type})


@pytest.fixture
def login_helper_async():
    return _async_login_and_set_cookie


@pytest.fixture
def login_helper_sync():
    return _sync_login_and_set_cookie
