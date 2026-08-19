import pytest
from app.tests.conftest import Credentials, create_room_async


@pytest.mark.anyio
async def test_private_room_access(async_client, login_helper_async, endpoints):
    # Bob creates a private room
    bob = Credentials().as_dict()
    await login_helper_async(async_client, bob["username"], bob["password"])
    r = await create_room_async(async_client, endpoints, "bobroom", "PRIVATE")
    assert r.status_code == 201

    # Alice logs in but is not a member
    alice = Credentials().as_dict()
    await login_helper_async(async_client, alice["username"], alice["password"])

    # Alice should be forbidden from viewing private room details
    r = await async_client.get(endpoints.api.rooms.room_name.room_detail(room_name="bobroom"))
    assert r.status_code == 403

    # Alice should not be able to delete Bob's room
    r = await async_client.delete(endpoints.api.rooms.room_name.room_delete(room_name="bobroom"))
    assert r.status_code == 403

    # Alice should not be able to kick members
    r = await async_client.post(endpoints.api.rooms.room_name.room_kick(room_name="bobroom"), json={"username": bob["username"]})
    assert r.status_code == 403

    # Alice trying to join should get application required or forbidden (403)
    r = await async_client.post(endpoints.api.rooms.room_join, json={"room_name": "bobroom"})
    assert r.status_code == 403


@pytest.mark.anyio
async def test_user_removed_while_session_still_valid(async_client, login_helper_async, endpoints):
    # Bob creates a public room and Alice joins
    bob = Credentials().as_dict()
    await login_helper_async(async_client, bob["username"], bob["password"])
    r = await create_room_async(async_client, endpoints, "pubroom", "PUBLIC")
    assert r.status_code == 201

    # Alice logs in and joins
    alice = Credentials().as_dict()
    await login_helper_async(async_client, alice["username"], alice["password"])
    r = await async_client.post(endpoints.api.rooms.room_join, json={"room_name": "pubroom"})
    assert r.status_code == 200

    # Now Bob (owner) kicks Alice
    await login_helper_async(async_client, bob["username"], bob["password"])
    r = await async_client.post(endpoints.api.rooms.room_name.room_kick(room_name="pubroom"), json={"username": alice["username"]})
    assert r.status_code == 200

    # Alice's session still has cookie; confirm she is now forbidden from room details
    await login_helper_async(async_client, alice["username"], alice["password"])
    r = await async_client.get(endpoints.api.rooms.room_name.room_detail(room_name="pubroom"))
    assert r.status_code == 403
