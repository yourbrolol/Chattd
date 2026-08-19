import json
import asyncio
import pytest
from starlette.testclient import WebSocketDisconnect
from sqlalchemy import select

from app.chat.models import ChatMessage, User
from app.core.database import SessionLocal
from app.tests.conftest import Credentials, create_room_sync


def clear_cookies(client):
    client.cookies.clear()


def query_messages(content: str):
    async def _q():
        async with SessionLocal() as session:
            stmt = select(ChatMessage).where(ChatMessage.content == content)
            res = await session.execute(stmt)
            return res.scalars().all()
    return asyncio.run(_q())


def test_ws_connect_without_cookie_is_rejected(sync_client, endpoints):
    clear_cookies(sync_client)
    with pytest.raises(WebSocketDisconnect):
        with sync_client.websocket_connect(endpoints.fe.ws_chat.format(room_name="roomx")):
            pass


def test_revoke_while_connected_prevents_message_persistence(sync_client, login_helper_sync, endpoints):
    # Setup: Bob creates public room
    bob = Credentials().as_dict()
    login_helper_sync(sync_client, bob["username"], bob["password"])
    r = create_room_sync(sync_client, endpoints, "publicroom", "PUBLIC")
    print("responce", r)
    assert r.status_code == 201

    # Alice registers, logs in, joins
    alice = Credentials().as_dict()
    login_helper_sync(sync_client, alice["username"], alice["password"])
    r = sync_client.post(endpoints.api.rooms.room_join, json={"room_name": "publicroom"})
    assert r.status_code == 200

    # Connect websocket as Alice
    login_helper_sync(sync_client, alice["username"], alice["password"])
    with sync_client.websocket_connect(endpoints.fe.ws_chat.format(room_name="publicroom")) as ws:
        # receive init
        init = ws.receive_text()
        assert "init" in init

        # Bob (owner) kicks Alice
        login_helper_sync(sync_client, bob["username"], bob["password"])
        r = sync_client.post(endpoints.api.rooms.room_name.room_kick(room_name="publicroom"), json={"username": alice["username"]})
        assert r.status_code == 200

        # Alice sends a message while still connected
        ws.send_text(json.dumps({"type": "chat_message", "message": "should_not_persist"}))

    # After connection closed/operation, ensure message not persisted
    msgs = query_messages("should_not_persist")
    assert len(msgs) == 0


def test_delete_account_while_connected_handles_gracefully(sync_client, login_helper_sync, endpoints):
    # Setup: owner creates room and user joins
    owner = Credentials().as_dict()
    login_helper_sync(sync_client, owner["username"], owner["password"])
    r = create_room_sync(sync_client, endpoints, "deleteroom", "PUBLIC")
    assert r.status_code == 201

    victim = Credentials().as_dict()
    login_helper_sync(sync_client, victim["username"], victim["password"])
    r = sync_client.post(endpoints.api.rooms.room_join, json={"room_name": "deleteroom"})
    assert r.status_code == 200

    # Connect websocket as victim
    login_helper_sync(sync_client, victim["username"], victim["password"])
    with sync_client.websocket_connect(endpoints.fe.ws_chat.format(room_name="deleteroom")) as ws:
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
