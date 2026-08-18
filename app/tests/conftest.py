import os
import asyncio
import pytest
import secrets

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
        # allow setting attributes during init
        object.__setattr__(self, "_frozen", False)
        object.__setattr__(self, "prefix", (prefix or "").rstrip("/"))

        if iterable:
            for key, value in iterable.items():
                # If a nested EndpointMap is provided, combine prefixes so
                # attribute access returns fully-qualified paths.
                # store child maps as-is; full prefixes are normalized later
                self[key] = value

        # freeze to prevent later mutation
        object.__setattr__(self, "_frozen", True)
    def __getattr__(self, key):
        # direct key
        try:
            value = self[key]
        except KeyError:
            # try placeholder key mapping: attribute `room_name` -> key `{room_name}`
            placeholder = f"{{{key}}}"
            if placeholder in self:
                value = self[placeholder]
            else:
                # helpful AttributeError listing available keys
                available = []
                for k in self.keys():
                    if isinstance(k, str) and k.startswith("{") and k.endswith("}"):
                        available.append(k[1:-1])
                    else:
                        available.append(k)
                raise AttributeError(f"'{key}' not found; available: {available}")

        if isinstance(value, EndpointMap):
            return value

        if isinstance(value, str):
            return Endpoint(self._resolve(value))

        # For any other stored value, return as-is.
        return value

    def __setattr__(self, key, value):
        # allow prefix and internal attrs
        if key == "prefix":
            object.__setattr__(self, key, (value or "").rstrip("/"))
            return
        if key == "_frozen":
            object.__setattr__(self, key, value)
            return

        if getattr(self, "_frozen", False):
            raise TypeError("EndpointMap is frozen and cannot be mutated")

        super().__setattr__(key, value)

    def __setitem__(self, key, value):
        if getattr(self, "_frozen", False):
            raise TypeError("EndpointMap is frozen and cannot be mutated")
        super().__setitem__(key, value)

    def _resolve(self, value):
        if value == "":
            return self.prefix or "/"

        candidate = value if value.startswith("/") else f"/{value}"
        if not self.prefix:
            return candidate
        if candidate.startswith(self.prefix):
            return candidate
        return f"{self.prefix}{candidate}"

    def _join_prefixes(self, base: str, child: str) -> str:
        """Join base and child prefixes into a single normalized prefix.

        Keeps leading slashes on child and strips trailing slashes.
        Examples:
        - base='' + child='/api' -> '/api'
        - base='/api' + child='/auth' -> '/api/auth'
        - base='/api' + child='auth' -> '/api/auth'
        - base='/api' + child='' -> '/api'
        """
        base = (base or "").rstrip("/")
        child = (child or "").rstrip("/")

        if not base and not child:
            return ""
        if not base:
            return child if child.startswith("/") else f"/{child}"
        if not child:
            return base
        # ensure child has leading slash
        child_candidate = child if child.startswith("/") else f"/{child}"
        return f"{base}{child_candidate}"

    def _normalize_prefixes(self, parent_prefix: str = ""):
        """Recursively join prefixes from parent down to children.

        This ensures nested EndpointMaps include the full path from the root.
        """
        # compute this node's absolute prefix
        self.prefix = self._join_prefixes(parent_prefix, self.prefix)
        for k, v in list(self.items()):
            if isinstance(v, EndpointMap):
                v._normalize_prefixes(self.prefix)


class Endpoint(str):
    """String-like endpoint with callable formatting.

    Example:
      ep = Endpoint('/api/rooms/{room_name}/')
      str(ep) -> '/api/rooms/{room_name}/'
      ep(room_name='x') -> '/api/rooms/x/'
    """

    def __new__(cls, fmt: str):
        obj = str.__new__(cls, fmt)
        obj.fmt = fmt
        return obj

    def __call__(self, /, *args, **kwargs):
        try:
            return self.fmt.format(*args, **kwargs)
        except Exception:
            return self.fmt


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
                        "room_name": EndpointMap(
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
                "users": EndpointMap(
                    prefix="/users",
                    iterable={
                        "user_detail": "/{user_id}"
                    },
                ),
                "applications": EndpointMap(
                    prefix="/applications",
                    iterable={
                        "application_apply": "",
                        "application_pending": "/pending",
                        "application_pending_room": "/pending/{room_name}",
                        "application_id": EndpointMap(
                            prefix="/{application_id}",
                            iterable={
                                "application_review": "/",
                            }
                        )
                    },
                ),
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

# Normalize prefixes so every nested EndpointMap has full absolute prefix.
ENDPOINTS._normalize_prefixes("")


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


class Credentials():
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        userlen: int = 8,
        passlen: int = 12
    ):
        _username, _password = self.initialize(userlen=userlen, passlen=passlen)
        self.username = username or _username
        self.password = password or _password
    def as_dict(self):
        return {'username': self.username, 'password': self.password}
    @staticmethod
    def initialize(
        userlen: int = 8,
        passlen: int = 12
    ):
        # Generate pseudo-random hexadecimal string of lenght n, for example: "a1ujcndihad"
        return secrets.token_hex(userlen), secrets.token_hex(passlen)