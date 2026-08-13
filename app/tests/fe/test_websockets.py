import json
import asyncio
import pytest
from starlette.testclient import TestClient, WebSocketDisconnect

from app.main import app
from app.core.database import init_db, SessionLocal
from sqlalchemy import select
from app.chat.models import ChatMessage, User


@pytest.fixture(scope="module", autouse=True)
def ensure_db():
    # Create tables for tests
    asyncio.run(init_db())


def register_and_login(client: TestClient, username: str, password: str):
    r = client.post("/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    cookie_value = json.dumps({"access_token": token})
    client.cookies.set("access_token", cookie_value)
    return token


def clear_cookies(client: TestClient):
    client.cookies.clear()


def query_messages(content: str):
    async def _q():
        async with SessionLocal() as session:
            stmt = select(ChatMessage).where(ChatMessage.content == content)
            res = await session.execute(stmt)
            return res.scalars().all()
    return asyncio.run(_q())


def test_ws_connect_without_cookie_is_rejected():
    with TestClient(app) as client:
        clear_cookies(client)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/chat/roomx/"):
                pass


def test_revoke_while_connected_prevents_message_persistence():
    with TestClient(app) as client:
        # Setup: Bob creates public room
        register_and_login(client, "bob_ws", "pw")
        r = client.post("/rooms", json={"room_name": "publicroom", "room_type": "PUBLIC"})
        assert r.status_code == 201

        # Alice registers, logs in, joins
        register_and_login(client, "alice_ws", "pw")
        r = client.post("/rooms/join", json={"room_name": "publicroom"})
        assert r.status_code == 200

        # Connect websocket as Alice
        token = register_and_login(client, "alice_ws", "pw")
        with client.websocket_connect("/ws/chat/publicroom/") as ws:
            # receive init
            init = ws.receive_text()
            assert "init" in init

            # Bob (owner) kicks Alice
            register_and_login(client, "bob_ws", "pw")
            r = client.post("/rooms/publicroom/kick", json={"username": "alice_ws"})
            assert r.status_code == 200

            # Alice sends a message while still connected
            ws.send_text(json.dumps({"type": "chat_message", "message": "should_not_persist"}))

        # After connection closed/operation, ensure message not persisted
        msgs = query_messages("should_not_persist")
        assert len(msgs) == 0


def test_delete_account_while_connected_handles_gracefully():
    with TestClient(app) as client:
        # Setup: owner creates room and user joins
        register_and_login(client, "owner_ws", "pw")
        r = client.post("/rooms", json={"room_name": "deleteroom", "room_type": "PUBLIC"})
        assert r.status_code == 201

        register_and_login(client, "victim_ws", "pw")
        r = client.post("/rooms/join", json={"room_name": "deleteroom"})
        assert r.status_code == 200

        # Connect websocket as victim
        register_and_login(client, "victim_ws", "pw")
        with client.websocket_connect("/ws/chat/deleteroom/") as ws:
            init = ws.receive_text()
            assert "init" in init

            # Delete victim directly from DB
            async def _delete():
                async with SessionLocal() as s:
                    stmt = select(User).where(User.username == "victim_ws")
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
