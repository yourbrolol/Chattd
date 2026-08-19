import pytest


@pytest.mark.anyio
async def test_create_list_search_rooms(async_client, endpoints, login_helper_async):
	"""Create room, list rooms for user, and search for rooms with query filtering."""
	pytest.skip("placeholder: implement create/list/search rooms tests")


@pytest.mark.anyio
async def test_room_rename_and_conflicts(async_client, endpoints, login_helper_async):
	"""PATCH /api/rooms/{room_name}: rename success; renaming to existing name returns name_taken."""
	pytest.skip("placeholder: implement room rename tests")


@pytest.mark.anyio
async def test_leave_and_delete_room_authorization(async_client, endpoints, login_helper_async):
	"""Leave room as member; delete room as owner; non-owner delete returns 403."""
	pytest.skip("placeholder: implement leave/delete authorization tests")
