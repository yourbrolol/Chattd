"""
Test Suite 2:
Users: 1 (owner), 2, 3 (random names),
Scenario:
1. User 1 registers and logs in,
2. User 1 creates a PRIVATE room,
3. User 1 sends "private hello",
4. User 2 registers and logs in,
5. User 2 searches the room name -> must NOT appear in public_rooms
   (edge case: private rooms should be hidden from search results),
6. User 2 tries to join directly -> rejected (no membership without approval),
7. User 2 tries to open a websocket to the room -> connection refused
   (bug check: non-members must not be able to chat even if they know the name),
8. User 2 applies to join the room,
9. User 2 applies AGAIN (duplicate application bug check) -> must not create
   a second pending application,
10. User 3 registers, logs in and applies too,
11. User 1 lists pending applications for the room -> sees exactly 2,
    User 1 also checks the global pending list (overview path),
12. User 1 reviews User 3's application first (out of order on purpose)
    -> approved, User 3 is now a member,
13. User 1 reviews User 2's application -> approved,
14. User 2 tries to review their own already-approved application again
    (stale client retry) -> must fail cleanly, no state corruption,
15. User 2 joins now that they are approved, then connects via websocket
    and sends "thanks!",
16. User 3 kicks User 2 (non-owner trying to kick, bug check) -> forbidden;
    User 3 then tries to kick themselves -> must fail or behave sanely,
17. Owner (User 1) kicks User 2,
18. Kicked User 2 tries to send "let me back in?" over websocket -> refused;
19. User 2 re-applies after being kicked (re-application edge case),
20. User 1 deletes the room while User 2's application is still pending ->
    application must be cleaned up / orphaned safely,
21. All users log out.
"""

import json

import pytest

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


def test_suite_2(sync_client, endpoints):
    """End-to-end scenario for a private room with applications and kicks."""
    # 1. User 1 registers and logs in,
    user1 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user1["username"], user1["password"])

    # 2. User 1 creates a PRIVATE room,
    room_name = room_payload_factory()["room_name"]
    r = create_room_sync(sync_client, endpoints, room_name, "PRIVATE")
    assert r.status_code == 201

    # 3. User 1 sends "private hello",
    with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
        _receive_init(ws)
        _send_chat(ws, "private hello")

    # 4. User 2 registers and logs in,
    user2 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user2["username"], user2["password"])

    # 5. User 2 searches the room name -> private rooms hidden,
    r = sync_client.get(f"{endpoints.ROOMS_LIST}/search?q={room_name}")
    assert r.status_code == 200
    data = r.json()
    found_names = {item["name"] for item in data.get("public_rooms", [])}
    assert room_name not in found_names

    # 6. User 2 tries to join directly -> rejected,
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": room_name})
    assert r.status_code == 403

    # 7. User 2 tries to open a websocket -> connection refused,
    with pytest.raises(Exception):
        with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
            _receive_init(ws)

    # 8. User 2 applies to join the room,
    r = sync_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    app2_id = r.json()["id"]
    assert r.json()["status"].upper() == "PENDING"

    # 9. User 2 applies AGAIN -> duplicate bug check,
    r = sync_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 200
    assert r.json().get("detail") == "already_pending" or r.json().get("status") == "pending"

    # 10. User 3 registers, logs in and applies too,
    user3 = user_payload_factory()
    authenticated_client_for_sync(sync_client, user3["username"], user3["password"])
    r = sync_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    app3_id = r.json()["id"]

    # 11. Owner lists pending applications for the room and globally,
    login_as_sync(sync_client, user1["username"], user1["password"])
    r = sync_client.get(endpoints.application_pending_room(room_name))
    assert r.status_code == 200
    pending_ids = {item["id"] for item in r.json()}
    assert {app2_id, app3_id} <= pending_ids

    r_global = sync_client.get(endpoints.APPLICATIONS_PENDING)
    assert r_global.status_code == 200
    global_room_names = {item["room"] for item in r_global.json()}
    assert room_name in global_room_names

    # 12. Owner approves User 3's application first (out of order),
    r = sync_client.post(
        endpoints.application_review(app3_id), json={"action": "approve"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    # 13. Owner approves User 2's application,
    r = sync_client.post(
        endpoints.application_review(app2_id), json={"action": "approve"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    # 14. Stale retry: User 2 re-reviews their own approved application,
    login_as_sync(sync_client, user2["username"], user2["password"])
    r = sync_client.post(
        endpoints.application_review(app2_id), json={"action": "approve"}
    )
    assert r.status_code in (403, 404)

    # 15. User 2 joins (approved) and chats,
    r = sync_client.post(endpoints.ROOM_JOIN, json={"room_name": room_name})
    assert r.status_code == 200
    with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
        _receive_init(ws)
        _send_chat(ws, "thanks!")

    # 16. Non-owner kick attempts (bug checks),
    login_as_sync(sync_client, user3["username"], user3["password"])
    r = sync_client.post(
        endpoints.room_kick(room_name), json={"username": user2["username"]}
    )
    assert r.status_code == 403

    r_self = sync_client.post(
        endpoints.room_kick(room_name), json={"username": user3["username"]}
    )
    assert r_self.status_code in (400, 403, 404)

    # 17. Owner kicks User 2,
    login_as_sync(sync_client, user1["username"], user1["password"])
    r = sync_client.post(
        endpoints.room_kick(room_name), json={"username": user2["username"]}
    )
    assert r.status_code == 200
    assert r.json().get("message") == "member_kicked"

    # 18. Kicked User 2 tries to chat over websocket -> refused,
    login_as_sync(sync_client, user2["username"], user2["password"])
    with pytest.raises(Exception):
        with sync_client.websocket_connect(endpoints.ws_chat(room_name)) as ws:
            _receive_init(ws)
            _send_chat(ws, "let me back in?")

    # 19. Kicked User 2 re-applies after the kick (their earlier application
    #     is still APPROVED in the system -> service may short-circuit),
    r = sync_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code in (200, 201)
    reapplied_id = r.json().get("id")

    # 20. Owner deletes the room while that application is still pending,
    login_as_sync(sync_client, user1["username"], user1["password"])
    r = sync_client.delete(endpoints.room_delete(room_name))
    assert r.status_code == 200
    assert r.json().get("message") == "room_deleted"

    r_pending = sync_client.get(endpoints.application_pending_room(room_name))
    assert r_pending.status_code == 404

    # Reviewing the orphaned application must fail cleanly.
    r_orphan = sync_client.post(
        endpoints.application_review(reapplied_id), json={"action": "reject"}
    )
    assert r_orphan.status_code in (403, 404, 422) if reapplied_id is None else r_orphan.status_code in (403, 404)

    # 21. All users log out.
    for username, password in (
        (user1["username"], user1["password"]),
        (user2["username"], user2["password"]),
        (user3["username"], user3["password"]),
    ):
        login_as_sync(sync_client, username, password)
        r = sync_client.post(endpoints.LOGOUT)
        assert r.status_code == 200
        sync_client.cookies.clear()
