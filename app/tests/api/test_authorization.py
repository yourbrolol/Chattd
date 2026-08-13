import pytest


@pytest.mark.anyio
async def test_alice_cannot_access_bobs_private_room(async_client, login_helper_async, endpoints):
    # Bob creates a private room
    await login_helper_async(async_client, "bob", "pw")
    r = await async_client.post(endpoints.api.room_create, json={"room_name": "bobroom", "room_type": "PRIVATE"})
    assert r.status_code == 201

    # Alice logs in but is not a member
    await login_helper_async(async_client, "alice", "pw")

    # Alice should be forbidden from viewing private room details
    r = await async_client.get(endpoints.api.room_detail.format(room_name="bobroom"))
    assert r.status_code == 403

    # Alice should not be able to delete Bob's room
    r = await async_client.delete(endpoints.api.room_delete.format(room_name="bobroom"))
    assert r.status_code == 403

    # Alice should not be able to kick members
    r = await async_client.post(endpoints.api.room_kick.format(room_name="bobroom"), json={"username": "bob"})
    assert r.status_code == 403

    # Alice trying to join should get application required or forbidden (403)
    r = await async_client.post(endpoints.api.room_join, json={"room_name": "bobroom"})
    assert r.status_code == 403


@pytest.mark.anyio
async def test_alice_removed_while_session_still_valid(async_client, login_helper_async, endpoints):
    # Bob creates a public room and Alice joins
    await login_helper_async(async_client, "bob2", "pw")
    r = await async_client.post(endpoints.api.room_create, json={"room_name": "pubroom", "room_type": "PUBLIC"})
    assert r.status_code == 201

    # Alice logs in and joins
    await login_helper_async(async_client, "alice2", "pw")
    r = await async_client.post(endpoints.api.room_join, json={"room_name": "pubroom"})
    assert r.status_code == 200

    # Now Bob (owner) kicks Alice
    await login_helper_async(async_client, "bob2", "pw")
    r = await async_client.post(endpoints.api.room_kick.format(room_name="pubroom"), json={"username": "alice2"})
    assert r.status_code == 200

    # Alice's session still has cookie; confirm she is now forbidden from room details
    await login_helper_async(async_client, "alice2", "pw")
    r = await async_client.get(endpoints.api.room_detail.format(room_name="pubroom"))
    assert r.status_code == 403
