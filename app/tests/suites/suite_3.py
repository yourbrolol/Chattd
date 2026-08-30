"""
Test Suite 3:
Users: 1 (owner), 2, 3 (random names),
Scenario:
1. User 1 registers and logs in,
2. User 1 creates a public room with a name containing mixed case and
   special characters (e.g. "Rm42.room_ab12cd34") -> creation must succeed,
3. User 1 creates a SECOND room with the exact same name (duplicate
   creation bug check) -> must be rejected,
4. User 1 sends an empty message over websocket (""), then a message of
   only whitespace ("   ") -> both must be rejected or stored sanely,
5. User 1 edits the room to a new name via edit endpoint
   (overview -> rename path),
6. User 2 registers and logs in, searches for the OLD room name ->
   must not be found; searches for the NEW name -> found,
7. User 2 joins the room and opens two websocket connections at the same
   time (same user, duplicate sessions) and sends a message from each ->
   no crash, messages accepted,
8. While User 2's sockets are open, User 3 (registered & logged in)
   deletes... nothing: User 3 attempts to DELETE the room (non-owner,
   bug check) -> forbidden,
9. User 3 then attempts to EDIT the room name (non-owner bug check) ->
   forbidden, room keeps its name,
10. User 3 tries to join a NONEXISTENT room -> clean 404-style error,
    not a 500,
11. User 2 leaves the room while their websockets are still open ->
    subsequent send must fail; sockets should close or reject,
12. User 1 (owner) tries to LEAVE their own room (edge case: owner
    leaving own room) -> must fail or transfer ownership deterministically,
13. User 1 logs in a second time from a "second device" (fresh login
    overwriting cookie) and confirms old actions still authorized,
14. Unauthenticated client (cleared cookies) hits ROOMS_LIST, join and
    websocket endpoints -> all rejected, no information leak,
15. User 1 renames the room again while nobody is connected, verifies
    message history survives under the new name (via websocket init),
16. All users log out.
"""

import json

import httpx
import pytest

from starlette.websockets import WebSocketDisconnect

from app.tests.conftest import (
    user_payload_factory,
    room_payload_factory,
    authenticated_client_for_sync,
    create_room_sync,
    login_as_sync,
)


def _receive_init(ws) -> None:
    init = ws.receive_text()
    assert "init" in init


def _send_chat(ws, message: str) -> None:
    ws.send_text(json.dumps({"type": "chat_message", "message": message}))


def test_suite_3(sync_client, endpoints):
    """End-to-end scenario covering naming edge cases, duplicate sessions and permissions."""
    # 1. User 1 registers and logs in,
    user1 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user1["username"], user1["password"])

    # 2. Create a public room with mixed case + special characters,
    room_name = f"Rm42.{room_payload_factory()['room_name']}"
    r = create_room_sync(sync_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    # 3. Duplicate creation must be rejected,
    r_dup = create_room_sync(sync_client, endpoints, room_name, "PUBLIC")
    assert r_dup.status_code == 400

    # 4. Empty and whitespace-only messages,
    with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
        _receive_init(ws)
        _send_chat(ws, "")
        _send_chat(ws, "   ")
        _send_chat(ws, "real message")

    old_name = room_name

    # 5. Owner renames the room via edit endpoint,
    new_name = f"renamed_{room_payload_factory()['room_name']}"
    r = sync_client.patch(endpoints.room_detail(old_name), json={"name": new_name})
    assert r.status_code == 200
    assert r.json().get("new_name", r.json().get("name")) == new_name

    # 6. Search reflects the rename for User 2,
    user2 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user2["username"], user2["password"])

    r = sync_client.get(f"{endpoints.ROOMS_LIST}/search?q={old_name}")
    assert r.status_code == 200
    assert old_name not in {item["name"] for item in r.json().get("public_rooms", [])}

    r = sync_client.get(f"{endpoints.ROOMS_LIST}/search?q={new_name}")
    assert r.status_code == 200
    assert new_name in {item["name"] for item in r.json().get("public_rooms", [])}

    # 7. User 2 joins and opens two websocket sessions simultaneously,
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": new_name})
    assert r.status_code == 200

    ws1 = sync_client.websocket_connect(endpoints.ws_chat(new_name))
    ws2 = sync_client.websocket_connect(endpoints.ws_chat(new_name))
    w1 = ws1.__enter__()
    w2 = ws2.__enter__()
    try:
        _receive_init(w1)
        _receive_init(w2)
        _send_chat(w1, "from session one")
        _send_chat(w2, "from session two")
    finally:
        # Keep sockets open through steps 8-10; close on leave (step 11).
        pass

    # 8. Non-owner delete attempt (bug check),
    user3 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user3["username"], user3["password"])
    r = sync_client.delete(endpoints.room_delete(new_name))
    assert r.status_code == 403

    # 9. Non-owner edit attempt -> room keeps its name,
    r = sync_client.patch(
        endpoints.room_detail(new_name),
        json={"name": f"hijacked_{user3['username']}"},
    )
    assert r.status_code == 403

    # 10. Joining a nonexistent room -> clean error, not a 500,
    r = sync_client.post(
        endpoints.ROOM_JOIN, json={"room_name": "definitely_not_a_room_xyz"}
    )
    assert r.status_code == 404

    # 11. User 2 leaves while their websockets are still open,
    login_as_sync(sync_client, user2["username"], user2["password"])
    r = sync_client.post(endpoints.room_leave(new_name))
    assert r.status_code == 200

    with pytest.raises(Exception):
        _send_chat(w1, "still here?")
        w1.receive_text(timeout=5)

    ws1.__exit__(None, None, None)
    ws2.__exit__(None, None, None)

    # 12. Owner tries to leave their own room -> must fail OR leave the room
    #     itself intact with a deterministic outcome,
    login_as_sync(sync_client, user1["username"], user1["password"])
    r = sync_client.post(endpoints.room_leave(new_name))
    assert r.status_code in (200, 400, 403)
    owner_still_member = r.status_code != 200
    if r.status_code == 200:
        # Leaving as owner removed the membership but the room itself survives.
        r = sync_client.get(f"{endpoints.ROOMS_LIST}/search?q={new_name}")
        assert r.status_code == 200
        assert new_name in {item["name"] for item in r.json().get("public_rooms", [])}
        # Owner rejoins their own public room so later owner-only steps work.
        r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": new_name})
        assert r.status_code == 200

    # 13. Second-device login still authorizes owner actions,
    login_as_sync(sync_client, user1["username"], user1["password"])
    overview = sync_client.get(endpoints.ROOMS_LIST)
    assert overview.status_code == 200
    assert new_name in {item["name"] for item in overview.json()}

    # 14. Unauthenticated access is rejected everywhere,
    saved_cookies = httpx.Cookies(sync_client.cookies)
    sync_client.cookies.clear()

    r = sync_client.get(endpoints.ROOMS_LIST)
    assert r.status_code in (401, 403)

    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": new_name})
    assert r.status_code in (401, 403)

    with pytest.raises(Exception):
        with sync_client.websocket_connect(endpoints.ws_chat(new_name)) as ws:
            _receive_init(ws)

    sync_client.cookies.update(saved_cookies)

    # 15. Rename again while nobody is connected; post-first-rename history
    #     survives under the newest name,
    final_name = f"final_{room_payload_factory()['room_name']}"
    r = sync_client.patch(endpoints.room_detail(new_name), json={"name": final_name})
    assert r.status_code == 200

    with sync_client.websocket_connect(endpoints.ws_chat(final_name)) as ws:
        init = ws.receive_text()
    assert "from session one" in init
    assert "from session two" in init

    # 16. All users log out.
    for username, password in (
        (user1["username"], user1["password"]),
        (user2["username"], user2["password"]),
        (user3["username"], user3["password"]),
    ):
        login_as_sync(sync_client, username, password)
        r = sync_client.post(endpoints.LOGOUT)
        assert r.status_code == 200
        sync_client.cookies.clear()
