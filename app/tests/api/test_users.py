import os
import base64
import pytest
from app.chat.services.users import get_user_avatar_base64, AVATAR_FILE_NOT_FOUND, USER_OK
from app.tests.conftest import user_db_factory, authenticated_client_for

@pytest.mark.anyio
async def test_user_profile(async_client, db_session, endpoints):
    """GET /api/users/{id} returns profile for existing user and 404 for missing id."""
    # Setup: Create Bob directly in DB
    bob = await user_db_factory(db_session, "bob", "bobpassword")
    
    # Login as Bob to have authentication credentials
    await authenticated_client_for(async_client, bob.username, bob.raw_password)

    # 1. Test Existing User Profile
    r = await async_client.get(endpoints.user_detail(bob.id))
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == bob.id
    assert data["username"] == bob.username

    # 2. Test Non-existent User Profile (e.g. 99999)
    r_missing = await async_client.get(endpoints.user_detail(99999))
    assert r_missing.status_code == 404
    assert r_missing.json().get("detail") == "not_found"


@pytest.mark.anyio
async def test_avatar_base64(db_session, tmp_path):
    """Avatar base64 helper returns None when no file is set, AVATAR_FILE_NOT_FOUND for missing files, and valid b64 when the file exists."""
    # Setup user
    bob = await user_db_factory(db_session, "bobavatar", "pass123")
    
    # 1. No avatar case
    b64, code = get_user_avatar_base64(bob)
    assert b64 is None
    assert code == USER_OK

    # 2. Avatar path set but file missing case
    bob.avatar = "avatars/missing.png"
    b64, code = get_user_avatar_base64(bob, media_dir=str(tmp_path))
    assert b64 is None
    assert code == AVATAR_FILE_NOT_FOUND

    # 3. Avatar path set and file exists case
    media_dir = tmp_path / "media"
    avatar_dir = media_dir / "avatars"
    os.makedirs(avatar_dir, exist_ok=True)
    avatar_file = avatar_dir / "bob.png"
    avatar_file.write_bytes(b"dummy_image_data")

    bob.avatar = "avatars/bob.png"
    b64, code = get_user_avatar_base64(bob, media_dir=str(media_dir))
    assert code == USER_OK
    assert b64 == base64.b64encode(b"dummy_image_data").decode("utf-8")

