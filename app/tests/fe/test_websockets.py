import json
import asyncio
import pytest
from starlette.testclient import WebSocketDisconnect
from sqlalchemy import select

from app.chat.models import ChatMessage, User
from app.core.database import SessionLocal
from app.tests.conftest import (
    user_payload_factory,
    create_room_sync,
    login_as_sync,
    authenticated_client_for_sync,
)


def clear_cookies(client):
    client.cookies.clear()


def query_messages(content: str):
    async def _q():
        async with SessionLocal() as session:
            stmt = select(ChatMessage).where(ChatMessage.content == content)
            res = await session.execute(stmt)
            return res.scalars().all()
    return asyncio.run(_q())


def test_ws_rejects_unauthenticated(sync_client, endpoints):
    """Connecting to the WebSocket without a session cookie results in immediate disconnect."""
    clear_cookies(sync_client)
    with pytest.raises(WebSocketDisconnect):
        with sync_client.websocket_connect(endpoints.ws_chat("roomx")):
            pass


def test_ws_kicked_user_message_not_persisted(sync_client, endpoints):
    """Messages sent by a kicked user over an open WebSocket connection are not saved to the DB."""
    # Setup: Bob creates public room
    bob = user_payload_factory()
    authenticated_client_for_sync(sync_client, bob["username"], bob["password"])
    r = create_room_sync(sync_client, endpoints, "publicroom", "PUBLIC")
    print("responce", r)
    assert r.status_code == 201

    # Alice registers, logs in, joins
    alice = user_payload_factory()
    authenticated_client_for_sync(sync_client, alice["username"], alice["password"])
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": "publicroom"})
    assert r.status_code == 200

    # Connect websocket as Alice
    login_as_sync(sync_client, alice["username"], alice["password"])
    with sync_client.websocket_connect(endpoints.ws_chat("publicroom")) as ws:
        # receive init
        init = ws.receive_text()
        assert "init" in init

        # Bob (owner) kicks Alice
        login_as_sync(sync_client, bob["username"], bob["password"])
        r = sync_client.post(endpoints.room_kick("publicroom"), json={"username": alice["username"]})
        assert r.status_code == 200

        # Alice sends a message while still connected
        ws.send_text(json.dumps({"type": "chat_message", "message": "should_not_persist"}))

    # After connection closed/operation, ensure message not persisted
    msgs = query_messages("should_not_persist")
    assert len(msgs) == 0


def test_ws_handles_account_deletion_gracefully(sync_client, endpoints):
    """Deleting an account while the user has an open WebSocket connection does not crash the server."""
    # Setup: owner creates room and user joins
    owner = user_payload_factory()
    authenticated_client_for_sync(sync_client, owner["username"], owner["password"])
    r = create_room_sync(sync_client, endpoints, "deleteroom", "PUBLIC")
    assert r.status_code == 201

    victim = user_payload_factory()
    authenticated_client_for_sync(sync_client, victim["username"], victim["password"])
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": "deleteroom"})
    assert r.status_code == 200

    # Connect websocket as victim
    login_as_sync(sync_client, victim["username"], victim["password"])
    with sync_client.websocket_connect(endpoints.ws_chat("deleteroom")) as ws:
        init = ws.receive_text()
        assert "init" in init


        # Delete victim directly from DB
        async def _delete():
            async with SessionLocal() as s:
                stmt = select(User).where(User.username == victim["username"])
                res = await s.execute(stmt)
                u = res.scalars().first()
                if u:
                    await s.delete(u)
                    await s.commit()
        asyncio.run(_delete())

        # Victim sends message after deletion
        ws.send_text(json.dumps({"type": "chat_message", "message": "post_delete"}))

    msgs = query_messages("post_delete")
    assert len(msgs) == 0

