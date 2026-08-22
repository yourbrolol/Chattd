import pytest

from app.tests.conftest import (
    user_payload_factory,
    create_room_async,
    authenticated_client_for,
    login_as,
)


@pytest.mark.anyio
async def test_create_list_search_rooms(async_client, endpoints):
    """Create rooms, list owned/joined rooms, and search by query."""
    # Register and login a user (owner)
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner["username"], owner["password"])

    # Create several rooms
    r = await create_room_async(async_client, endpoints, "alpha_room", "PUBLIC")
    assert r.status_code == 201
    r = await create_room_async(async_client, endpoints, "beta_room", "PUBLIC")
    assert r.status_code == 201
    r = await create_room_async(async_client, endpoints, "alphabeta", "PUBLIC")
    assert r.status_code == 201

    # List rooms for the owner (should include all three)
    r = await async_client.get(endpoints.ROOMS_LIST)
    assert r.status_code == 200
    names = {item["name"] for item in r.json()}
    assert {"alpha_room", "beta_room", "alphabeta"}.issubset(names)

    # Search for rooms matching 'alpha' should return joined rooms containing those names
    r = await async_client.get(f"{endpoints.ROOMS_LIST}/search?q=alpha")
    assert r.status_code == 200
    data = r.json()
    joined_names = {it["name"] for it in data.get("joined_rooms", [])}
    assert "alpha_room" in joined_names
    assert "alphabeta" in joined_names


@pytest.mark.anyio
async def test_room_rename_and_conflicts(async_client, endpoints):
    """PATCH /api/rooms/{room_name}: rename success; renaming to existing name returns name_taken."""
    # Create owner and two rooms
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner["username"], owner["password"])

    r = await create_room_async(async_client, endpoints, "room_one", "PUBLIC")
    assert r.status_code == 201
    r = await create_room_async(async_client, endpoints, "room_two", "PUBLIC")
    assert r.status_code == 201

    # Successful rename of room_one -> renamed_room
    resp = await async_client.patch(endpoints.room_detail("room_one"), json={"name": "renamed_room"})
    assert resp.status_code == 200
    assert resp.json().get("new_name") == "renamed_room"

    # Attempt to rename renamed_room -> room_two (name already taken)
    resp_conflict = await async_client.patch(endpoints.room_detail("renamed_room"), json={"name": "room_two"})
    assert resp_conflict.status_code == 400
    assert resp_conflict.json().get("detail") == "name_taken"


@pytest.mark.anyio
async def test_leave_and_delete_room_authorization(async_client, endpoints):
    """Leave room as member; delete room as owner; non-owner delete returns 403."""
    # Owner creates a public room
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner["username"], owner["password"])
    r = await create_room_async(async_client, endpoints, "deletable_room", "PUBLIC")
    assert r.status_code == 201

    # Another user joins the room
    member = user_payload_factory()
    await authenticated_client_for(async_client, member["username"], member["password"])
    join_resp = await async_client.post(endpoints.ROOM_JOIN, json={"room_name": "deletable_room"})
    assert join_resp.status_code == 200

    # Member leaves the room
    leave_resp = await async_client.post(endpoints.room_leave("deletable_room"))
    assert leave_resp.status_code == 200
    assert leave_resp.json().get("message") == "left_room"

    # Non-owner (member user) cannot delete the room
    del_resp_non_owner = await async_client.delete(endpoints.room_delete("deletable_room"))
    assert del_resp_non_owner.status_code == 403

    # Owner deletes the room
    await login_as(async_client, owner["username"], owner["password"])
    del_resp_owner = await async_client.delete(endpoints.room_delete("deletable_room"))
    assert del_resp_owner.status_code == 200
    assert del_resp_owner.json().get("message") == "room_deleted"
