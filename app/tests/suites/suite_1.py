"""
Test Suite 1:
Users: 1, 2 (random names),
Scenario:
1. User 1 registers and logs in,
2. User 1 creates a new public room
3. User 1 sends "Hello!",
4. User 2 registers and logs in,
5. User 2 searches the room name,
6. If found, User 2 joins the room (2 times, bug check),
7. User 2 sends "Hello there!",
8. User 1 deletes the room (overview -> delete),
9. User 2 tries to send "Hello?",
10. User 2 tries to open overview, then leave,
11. User 2 logs out,
12. User 1 logs out.
"""

import json

import pytest

from app.tests.conftest import (
    user_payload_factory,
    room_payload_factory,
    create_room_sync,
    login_as_sync,
)


def _receive_init(ws) -> None:
    init = ws.receive_text()
    assert "init" in init


def _send_chat(ws, message: str) -> None:
    ws.send_text(json.dumps({"type": "chat_message", "message": message}))


def test_suite_1(sync_client, endpoints):
    """End-to-end scenario for two users sharing one public room."""
    # 1. User 1 registers and logs in,
    user1 = user_payload_factory()
    login_as_sync(sync_client, user1["username"], user1["password"])

    # 2. User 1 creates a new public room
    room_name = room_payload_factory()["room_name"]
    r = create_room_sync(sync_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    # 3. User 1 sends "Hello!",
    with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
        _receive_init(ws)
        _send_chat(ws, "Hello!")

    # 4. User 2 registers and logs in,
    user2 = user_payload_factory()
    login_as_sync(sync_client, user2["username"], user2["password"])

    # 5. User 2 searches the room name,
    r = sync_client.get(f"{endpoints.ROOMS_LIST}/search?q={room_name}")
    assert r.status_code == 200
    data = r.json()
    found_names = {item["name"] for item in data.get("joined_rooms", [])}
    assert room_name in found_names

    # 6. If found, User 2 joins the room (2 times, bug check),
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": room_name})
    assert r.status_code == 200
    r_again = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": room_name})
    assert r_again.status_code == 200

    # 7. User 2 sends "Hello there!",
    with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
        _receive_init(ws)
        _send_chat(ws, "Hello there!")

    # 8. User 1 deletes the room (overview -> delete),
    login_as_sync(sync_client, user1["username"], user1["password"])
    overview = sync_client.get(endpoints.ROOMS_LIST)
    assert overview.status_code == 200
    owned_names = {item["name"] for item in overview.json()}
    assert room_name in owned_names

    r = sync_client.delete(endpoints.room_delete(room_name))
    assert r.status_code == 200
    assert r.json().get("message") == "room_deleted"

    # 9. User 2 tries to send "Hello?",
    login_as_sync(sync_client, user2["username"], user2["password"])
    with pytest.raises(Exception):
        with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
            _receive_init(ws)
            _send_chat(ws, "Hello?")

    # 10. User 2 tries to open overview, then leave,
    overview = sync_client.get(endpoints.ROOMS_LIST)
    assert overview.status_code == 200
    member_names = {item["name"] for item in overview.json()}
    assert room_name not in member_names

    r = sync_client.post(endpoints.room_leave(room_name))
    assert r.status_code == 404

    # 11. User 2 logs out,
    r = sync_client.post(endpoints.LOGOUT)
    assert r.status_code == 200
    sync_client.cookies.clear()

    # 12. User 1 logs out.
    login_as_sync(sync_client, user1["username"], user1["password"])
    r = sync_client.post(endpoints.LOGOUT)
    assert r.status_code == 200
    sync_client.cookies.clear()
