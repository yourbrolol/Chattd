import pytest
from app.tests.fixtures import app

class Routes:
    # Auth
    REGISTER = "/api/auth/register"
    LOGIN = "/api/auth/login"
    LOGOUT = "/api/auth/logout"

    # Rooms
    ROOMS_LIST = "/api/rooms"
    ROOM_CREATE = "/api/rooms"
    ROOM_JOIN = "/api/rooms/join"

    @staticmethod
    def room_detail(room_name: str) -> str:
        return f"/api/rooms/{room_name}/"

    @staticmethod
    def room_leave(room_name: str) -> str:
        return f"/api/rooms/{room_name}/leave"

    @staticmethod
    def room_delete(room_name: str) -> str:
        return f"/api/rooms/{room_name}/delete"

    @staticmethod
    def room_kick(room_name: str) -> str:
        return f"/api/rooms/{room_name}/kick"

    # Users
    @staticmethod
    def user_detail(user_id) -> str:
        return f"/api/users/{user_id}"

    # Applications
    APPLICATIONS_APPLY = "/api/applications"
    APPLICATIONS_PENDING = "/api/applications/pending"

    @staticmethod
    def application_pending_room(room_name: str) -> str:
        return f"/api/applications/pending/{room_name}"

    @staticmethod
    def application_review(application_id) -> str:
        return f"/api/applications/{application_id}/review"

    # WebSockets
    @staticmethod
    def ws_chat(room_name: str) -> str:
        return f"/ws/chat/{room_name}/"


async def _async_login_and_set_cookie(client, username, password):
    await client.post(Routes.REGISTER, json={"username": username, "password": password})
    r = await client.post(Routes.LOGIN, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


def _sync_login_and_set_cookie(client, username, password):
    client.post(Routes.REGISTER, json={"username": username, "password": password})
    r = client.post(Routes.LOGIN, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


async def login_as(client, username, password):
    """Logs in an already registered user and sets cookie on client."""
    r = await client.post(Routes.LOGIN, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


def login_as_sync(client, username, password):
    """Sync version of login_as."""
    r = client.post(Routes.LOGIN, json={"username": username, "password": password})
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


def create_room_sync(client, routes, room_name, room_type):
    return client.post(routes.ROOM_CREATE, json={"room_name": room_name, "room_type": room_type})


async def create_room_async(client, routes, room_name, room_type):
    return await client.post(routes.ROOM_CREATE, json={"room_name": room_name, "room_type": room_type})


@pytest.fixture
def login_helper_async():
    return _async_login_and_set_cookie


@pytest.fixture
def login_helper_sync():
    return _sync_login_and_set_cookie

