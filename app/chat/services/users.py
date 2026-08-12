import os
import base64
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.chat.models import User
from app.chat.schemas.users import SettingsEditResponse

USER_OK = "ok"
USER_NOT_FOUND = "not_found"
AVATAR_FILE_NOT_FOUND = "avatar_file_not_found"

async def get_user_profile_data(db: AsyncSession, user_id: int) -> Tuple[Optional[dict], str]:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        return None, USER_NOT_FOUND

    avatar_url = f"/media/{user.avatar}" if user.avatar else None

    data = {
        "id": user.id,
        "username": user.username,
        "avatar": avatar_url,
    }
    return data, USER_OK


async def update_user_settings(
    db: AsyncSession,
    current_user: User,
    username: Optional[str],
    avatar: Optional[object],
    media_dir: str = "media",
    avatar_dir: Optional[str] = None,
) -> Tuple[Optional[dict], str]:
    username_changed = False
    avatar_changed = False

    new_username = (username or "").strip()
    if new_username and new_username != current_user.username:
        stmt = select(User).where(User.username == new_username)
        result = await db.execute(stmt)
        if result.scalars().first():
            return None, "username_taken"
        current_user.username = new_username
        username_changed = True

    if avatar is not None:
        content = await avatar.read()
        if len(content) > 2 * 1024 * 1024:
            return None, "file_too_large"

        filename = avatar.filename or ""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            return None, "invalid_format"

        avatar_path = avatar_dir or os.path.join(media_dir, "avatars")
        os.makedirs(avatar_path, exist_ok=True)

        if current_user.avatar:
            old_path = os.path.join(media_dir, current_user.avatar)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        db_filename = f"avatars/user_{current_user.id}.{ext}"
        new_path = os.path.join(media_dir, db_filename)
        with open(new_path, "wb") as f:
            f.write(content)

        current_user.avatar = db_filename
        avatar_changed = True

    if not username_changed and not avatar_changed:
        return None, "no_changes"

    await db.commit()
    return {
        "success": True,
        "avatar_url": f"/media/{current_user.avatar}" if current_user.avatar else None,
    }, USER_OK


def get_user_avatar_base64(user: User, media_dir: str = "media") -> Tuple[Optional[str], str]:
    if not user.avatar:
        return None, USER_OK

    # Build local path
    file_path = os.path.join(media_dir, user.avatar)
    if not os.path.exists(file_path):
        return None, AVATAR_FILE_NOT_FOUND

    try:
        with open(file_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
        return encoded_string, USER_OK
    except IOError:
        return None, AVATAR_FILE_NOT_FOUND
