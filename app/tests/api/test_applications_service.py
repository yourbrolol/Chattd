import pytest

from app.tests.conftest import (
    user_payload_factory,
    create_room_async,
    login_as,
    authenticated_client_for,
)


@pytest.mark.anyio
async def test_listing_apps(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_listing"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    # register and login as applicant
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])

    # apply to room
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201

    # login as owner and list pending applications
    await login_as(async_client, owner['username'], owner['password'])
    r = await async_client.get(endpoints.APPLICATIONS_PENDING)
    assert r.status_code == 200
    data = r.json()
    assert any(item.get("applicant") == applicant['username'] for item in data)


@pytest.mark.anyio
async def test_listing_room(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_listing_room"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201

    await login_as(async_client, owner['username'], owner['password'])
    r = await async_client.get(endpoints.application_pending_room(room_name))
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0].get("room") == room_name


@pytest.mark.anyio
async def test_applying(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_apply"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    data = r.json()
    assert data.get("room") == room_name
    assert data.get("status") == "PENDING"


@pytest.mark.anyio
async def test_applying_to_nonexistent(async_client, endpoints):
    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])

    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": "no_such_room"})
    assert r.status_code == 404


@pytest.mark.anyio
async def test_reapplying(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_reapply"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])

    r1 = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r1.status_code == 201

    r2 = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    # second attempt should return 200 with already_pending detail
    assert r2.status_code == 200
    assert r2.json().get("detail") == "already_pending"


@pytest.mark.anyio
async def test_member_reapplying(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_member_reapply"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    member = user_payload_factory()
    await authenticated_client_for(async_client, member['username'], member['password'])

    # Join the public room to become a member
    r = await async_client.post(endpoints.ROOM_JOIN, json={"room_name": room_name})
    assert r.status_code == 200

    # Now applying should be rejected as already_member
    r2 = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r2.status_code == 400
    assert r2.json().get("detail") == "already_member"


@pytest.mark.anyio
async def test_accepting_app(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_accept"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    app_id = r.json().get("id")

    # Owner approves
    await login_as(async_client, owner['username'], owner['password'])
    r = await async_client.post(endpoints.application_review(app_id), json={"action": "approve"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "APPROVED"

    # Verify membership by fetching room details as owner
    r = await async_client.get(endpoints.room_detail(room_name))
    assert r.status_code == 200
    members = r.json().get("members_data", [])
    assert any(m.get("username") == applicant['username'] for m in members)


@pytest.mark.anyio
async def test_rejecting_app(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_reject"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    app_id = r.json().get("id")

    # Owner rejects
    await login_as(async_client, owner['username'], owner['password'])
    r = await async_client.post(endpoints.application_review(app_id), json={"action": "reject"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "REJECTED"

    # Ensure applicant is not a member
    r = await async_client.get(endpoints.room_detail(room_name))
    assert r.status_code == 200
    members = r.json().get("members_data", [])
    assert not any(m.get("username") == applicant['username'] for m in members)


@pytest.mark.anyio
async def test_unauthorized_accepting(async_client, endpoints):
    owner = user_payload_factory()
    await authenticated_client_for(async_client, owner['username'], owner['password'])

    room_name = "testroom_unauth_accept"
    r = await create_room_async(async_client, endpoints, room_name, "PUBLIC")
    assert r.status_code == 201

    applicant = user_payload_factory()
    await authenticated_client_for(async_client, applicant['username'], applicant['password'])
    r = await async_client.post(endpoints.APPLICATIONS_APPLY, json={"room_name": room_name})
    assert r.status_code == 201
    app_id = r.json().get("id")

    # Another user (not owner) attempts to approve
    other = user_payload_factory()
    await authenticated_client_for(async_client, other['username'], other['password'])
    r = await async_client.post(endpoints.application_review(app_id), json={"action": "approve"})
    assert r.status_code == 403