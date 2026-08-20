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
    Routes,
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
    "Routes",
    "routes",
    "endpoints",
    "endpts",
]


@pytest.fixture
def routes():
    return Routes


@pytest.fixture
def endpoints():
    return Routes


@pytest.fixture
def endpts():
    return Routes