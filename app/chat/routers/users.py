import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.users import UserProfileResponse, SettingsEditResponse
from app.chat.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])

MEDIA_DIR = "media"
AVATAR_DIR = os.path.join(MEDIA_DIR, "avatars")

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data, code = await users_service.get_user_profile_data(db, user_id)
    if code == users_service.USER_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    return {
        "id": data["id"],
        "username": data["username"],
        "avatar_url": data["avatar"]
    }

@router.post("/settings", response_model=SettingsEditResponse)
async def edit_settings(
    username: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    username_changed = False
    avatar_changed = False

    new_username = (username or "").strip()
    if new_username and new_username != current_user.username:
        # Check uniqueness
        stmt = select(User).where(User.username == new_username)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="This username is already taken.")
        current_user.username = new_username
        username_changed = True

    if avatar:
        # File size check: 2MB
        content = await avatar.read()
        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds limit of 2MB")

        filename = avatar.filename or ""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed."
            )

        # Create avatar dir if not exist
        os.makedirs(AVATAR_DIR, exist_ok=True)

        # Remove old avatar file if exists
        if current_user.avatar:
            old_path = os.path.join(MEDIA_DIR, current_user.avatar)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        # Save new avatar file
        db_filename = f"avatars/user_{current_user.id}.{ext}"
        new_path = os.path.join(MEDIA_DIR, db_filename)
        with open(new_path, "wb") as f:
            f.write(content)

        current_user.avatar = db_filename
        avatar_changed = True

    if username_changed or avatar_changed:
        await db.commit()
    else:
        raise HTTPException(status_code=400, detail="No changes detected.")

    return {
        "success": True,
        "avatar_url": f"/media/{current_user.avatar}" if current_user.avatar else None
    }
