from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.users import UserProfileResponse, SettingsEditResponse
from app.chat.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])

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
    data, code = await users_service.update_user_settings(db, current_user, username, avatar)

    if code == "username_taken":
        raise HTTPException(status_code=400, detail="This username is already taken.")
    if code == "file_too_large":
        raise HTTPException(status_code=400, detail="File size exceeds limit of 2MB")
    if code == "invalid_format":
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed."
        )
    if code == "no_changes":
        raise HTTPException(status_code=400, detail="No changes detected.")

    return data
