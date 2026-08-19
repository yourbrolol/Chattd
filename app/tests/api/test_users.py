import pytest


@pytest.mark.anyio
async def test_get_user_profile_existing_and_missing(async_client, endpoints):
	"""GET /api/users/{user_id}: returns user profile for existing user and 404 for nonexistent user."""
	pytest.skip("placeholder: implement GET user profile test")


@pytest.mark.anyio
async def test_get_user_avatar_base64_returns_base64_or_not_found(db_session):
	"""`get_user_avatar_base64` should return base64 string when avatar exists, else AVATAR_FILE_NOT_FOUND."""
	pytest.skip("placeholder: implement avatar base64 test")


def test_get_user_profile_returns_profile():
	"""GET /api/users/{user_id} should return a user profile (id, username, avatar_url) when the user exists."""
	assert True


def test_get_user_not_found_returns_404():
	"""GET /api/users/{user_id} should return 404 when the user does not exist."""
	assert True


def test_get_user_avatar_base64_returns_string_when_exists():
	"""`get_user_avatar_base64` should return a base64 string when the user's avatar file exists, otherwise an error code."""
	assert True
