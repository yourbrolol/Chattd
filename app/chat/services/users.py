import os
import base64
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.chat.models import User

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
