import json
import pytest

from app.chat.models import User
from app.core.database import SessionLocal


async def login_and_set_cookie(client, username, password):
    await client.post("/auth/register", json={"username": username, "password": password})
    r = await client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    cookie_value = json.dumps({"access_token": token})
    client.cookies.set("access_token", cookie_value)
    return token


@pytest.mark.anyio
async def test_alice_cannot_access_bobs_private_room(client):
    # Bob creates a private room
    await login_and_set_cookie(client, "bob", "pw")
    r = await client.post("/rooms", json={"room_name": "bobroom", "room_type": "PRIVATE"})
    assert r.status_code == 201

    # Alice logs in but is not a member
    await login_and_set_cookie(client, "alice", "pw")

    # Alice should be forbidden from viewing private room details
    r = await client.get("/rooms/bobroom")
    assert r.status_code == 403

    # Alice should not be able to delete Bob's room
    r = await client.delete("/rooms/bobroom/delete")
    assert r.status_code == 403

    # Alice should not be able to kick members
    r = await client.post("/rooms/bobroom/kick", json={"username": "bob"})
    assert r.status_code == 403

    # Alice trying to join should get application required or forbidden (403)
    r = await client.post("/rooms/join", json={"room_name": "bobroom"})
    assert r.status_code == 403


@pytest.mark.anyio
async def test_alice_removed_while_session_still_valid(client):
    # Bob creates a public room and Alice joins
    await login_and_set_cookie(client, "bob2", "pw")
    r = await client.post("/rooms", json={"room_name": "pubroom", "room_type": "PUBLIC"})
    assert r.status_code == 201

    # Alice logs in and joins
    await login_and_set_cookie(client, "alice2", "pw")
    r = await client.post("/rooms/join", json={"room_name": "pubroom"})
    assert r.status_code == 200

    # Now Bob (owner) kicks Alice
    await login_and_set_cookie(client, "bob2", "pw")
    r = await client.post("/rooms/pubroom/kick", json={"username": "alice2"})
    assert r.status_code == 200

    # Alice's session still has cookie; confirm she is now forbidden from room details
    await login_and_set_cookie(client, "alice2", "pw")
    r = await client.get("/rooms/pubroom")
    assert r.status_code == 403
