import os
import base64
from django.contrib.auth import get_user_model

User = get_user_model()

USER_OK = "ok"
USER_NOT_FOUND = "not_found"
AVATAR_FILE_NOT_FOUND = "avatar_file_not_found"

def get_user_avatar_base64(user) -> tuple[str | None, str]:
    """
    Safely reads a user's avatar from disk and converts it to base64.
    Returns a tuple of (base64_string, status_code).
    """
    if not user.avatar:
        return None, USER_OK

    file_path = user.avatar.path
    if not os.path.exists(file_path):
        return None, AVATAR_FILE_NOT_FOUND

    try:
        with open(file_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
        return encoded_string, USER_OK
    except IOError:
        return None, AVATAR_FILE_NOT_FOUND

def get_user_profile_data(user_id: int) -> tuple[dict | None, str]:
    """
    Fetches a user profile and packages its serialized data safely.
    Returns a tuple of (data_dict, status_code).
    """
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None, USER_NOT_FOUND

    avatar_data, avatar_status = get_user_avatar_base64(user)

    data = {
        "id": user.id,
        "username": user.username,
        "avatar": avatar_data,
    }
    return data, USER_OK