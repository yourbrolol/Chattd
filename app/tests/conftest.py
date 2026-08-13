import os
import asyncio
import pytest

from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient

# Ensure default testing environment
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.main import app
from app.core.database import init_db, SessionLocal


HOST = "http://127.0.0.1:8000/"


class EndpointMap(dict):
    """Dict-like container with nested attribute access for endpoint strings."""

    def __init__(self, prefix="", iterable=None):
        super().__init__()
        self.prefix = prefix.rstrip("/")
        if iterable:
            for key, value in iterable.items():
                self[key] = value

    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

        if isinstance(value, EndpointMap):
            return value

        if isinstance(value, str):
            return self._resolve(value)

        print(value)
        return value

    def __setattr__(self, key, value):
        if key == "prefix":
            object.__setattr__(self, key, value.rstrip("/"))
            return
        super().__setattr__(key, value)

    def _resolve(self, value):
        if value == "":
            return self.prefix or "/"

        candidate = value if value.startswith("/") else f"/{value}"
        if not self.prefix:
            return candidate
        if candidate.startswith(self.prefix):
            return candidate
        return f"{self.prefix}{candidate}"


ENDPOINTS = EndpointMap(
    prefix="",
    iterable={
        "api": EndpointMap(
            prefix="/api",
            iterable={
                "auth": EndpointMap(
                    prefix="/auth",
                    iterable={
                        "register": "register",
                        "login": "login",
                        "logout": "logout",
                    },
                ),
                "rooms": EndpointMap(
                    prefix="/rooms",
                    iterable={
                        "room_create": "/",
                        "room_join": "/join",
                        "room_list": "/",
                        "{room_name}": EndpointMap(
                            prefix="/{room_name}",
                            iterable={
                                "room_detail": "/",
                                "room_leave": "/leave",
                                "room_delete": "/delete",
                                "room_edit": "/",
                                "room_kick": "/kick",
                            }
                        )
                    },
                ),
                "user_detail": "/users/{user_id}",
                "application_apply": "/applications",
                "application_review": "/applications/{application_id}/review",
                "application_pending": "/applications/pending",
                "application_pending_room": "/applications/pending/{room_name}",
            },
        ),
        "fe": EndpointMap(
            prefix="",
            iterable={
                "ws_chat": "/ws/chat/{room_name}/",
            },
        ),
    },
)


@pytest.fixture(scope="session", autouse=True)
def init_database():
    # Create DB tables once per test session
    asyncio.run(init_db())


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


@pytest.fixture
def endpoints():
    return ENDPOINTS


@pytest.fixture
def endpts():
    return ENDPOINTS


async def _async_login_and_set_cookie(client, username, password):
    await client.post(ENDPOINTS.api.auth.register, json={"username": username, "password": password})
    r = await client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


def _sync_login_and_set_cookie(client, username, password):
    client.post(ENDPOINTS.api.auth.register, json={"username": username, "password": password})
    r = client.post(ENDPOINTS.api.auth.login, json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.set("access_token", token)
    return token


@pytest.fixture
def login_helper_async():
    return _async_login_and_set_cookie


@pytest.fixture
def login_helper_sync():
    return _sync_login_and_set_cookie
