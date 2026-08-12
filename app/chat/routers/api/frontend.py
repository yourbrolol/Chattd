from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.users import SettingsEditResponse
from app.chat.services import users as users_service

router = APIRouter(tags=["frontend2"])

@router.post("/settings/edit/", response_model=SettingsEditResponse)
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
