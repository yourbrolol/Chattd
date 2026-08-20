import pytest
from app.tests.fixtures import init_database, async_client, sync_client, db_session
from app.tests.factories import (
    Credentials,
    user_payload_factory,
    user_db_factory,
    room_payload_factory,
    room_db_factory,
    member_db_factory,
    application_db_factory,
)
from app.tests.helpers import (
    login_helper_async,
    login_helper_sync,
    create_room_async,
    create_room_sync,
    login_as,
    login_as_sync,
    authenticated_client_for,
    authenticated_client_for_sync,
)

# Re-export them so tests importing from conftest don't break immediately
__all__ = [
    "init_database",
    "async_client",
    "sync_client",
    "db_session",
    "Credentials",
    "login_helper_async",
    "login_helper_sync",
    "create_room_async",
    "create_room_sync",
    "user_payload_factory",
    "user_db_factory",
    "room_payload_factory",
    "room_db_factory",
    "member_db_factory",
    "application_db_factory",
    "login_as",
    "login_as_sync",
    "authenticated_client_for",
    "authenticated_client_for_sync",
    "ENDPOINTS",
    "endpoints",
    "endpts",
]

class EndpointMap(dict):
    def __init__(self, prefix="", iterable=None):
        super().__init__()
        object.__setattr__(self, "_frozen", False)
        object.__setattr__(self, "prefix", (prefix or "").rstrip("/"))
        if iterable:
            for key, value in iterable.items():
                self[key] = value
        object.__setattr__(self, "_frozen", True)

    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError:
            placeholder = f"{{{key}}}"
            if placeholder in self:
                value = self[placeholder]
            else:
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
        return value

    def __setattr__(self, key, value):
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
        base = (base or "").rstrip("/")
        child = (child or "").rstrip("/")
        if not base and not child:
            return ""
        if not base:
            return child if child.startswith("/") else f"/{child}"
        if not child:
            return base
        child_candidate = child if child.startswith("/") else f"/{child}"
        return f"{base}{child_candidate}"

    def _normalize_prefixes(self, parent_prefix: str = ""):
        self.prefix = self._join_prefixes(parent_prefix, self.prefix)
        for k, v in list(self.items()):
            if isinstance(v, EndpointMap):
                v._normalize_prefixes(self.prefix)


class Endpoint(str):
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

ENDPOINTS._normalize_prefixes("")

@pytest.fixture
def endpoints():
    return ENDPOINTS

@pytest.fixture
def endpts():
    return ENDPOINTS