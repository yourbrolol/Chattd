import pytest


@pytest.mark.anyio
async def test_edit_settings_username_change_and_conflict(async_client, endpoints, login_helper_async):
	"""POST /api/frontend/settings/edit/: changes username when available; returns 400 when username_taken."""
	pytest.skip("placeholder: implement username change tests")


@pytest.mark.anyio
async def test_edit_settings_avatar_upload_valid_and_invalid(async_client, endpoints, login_helper_async, tmp_path):
	"""POST /api/frontend/settings/edit/: accepts valid avatar upload and rejects invalid/oversized files."""
	pytest.skip("placeholder: implement avatar upload tests")
