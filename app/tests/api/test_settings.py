import pytest

from app.tests.conftest import user_db_factory, db_session, Credentials


@pytest.mark.anyio
async def test_edit_settings_username_change_and_conflict(async_client, db_session, endpoints, login_helper_async):
    """POST /api/settings/edit/: changes username when available; returns 400 when username_taken."""
    # Log in as user1
    user1_cred = Credentials("user1", None)
    user1 = await login_helper_async(async_client, user1_cred.username, user1_cred.password)
    token1 = user1
    
    user2_cred = Credentials("user2", None)
    user2 = await user_db_factory(db_session, user2_cred.username, user2_cred.password)

    # Change username to a new one
    new_username = "new_user1"
    response = await async_client.post(
        endpoints.EDIT_SETTINGS,
        data={"username": new_username}
    )
    assert response.status_code == 200

    # Attempt to change username to an existing one (user2)
    response_conflict = await async_client.post(
        endpoints.EDIT_SETTINGS,
        data={"username": "user2"}
    )
    assert response_conflict.status_code == 400


@pytest.mark.anyio
async def test_edit_settings_avatar_upload_valid_and_invalid(async_client, endpoints, login_helper_async, tmp_path):
    """POST /api/settings/edit/: accepts valid avatar upload and rejects invalid/oversized files."""
    pytest.skip("placeholder: implement avatar upload tests")
