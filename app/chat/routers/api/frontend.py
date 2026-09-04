from fastapi import Depends, UploadFile, File, Form
from app.core.router import APIRouter
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.users import SettingsEditResponse
from app.chat.services import users as users_service
from app.chat.errors import AppError, ErrorCode

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
        raise AppError(ErrorCode.USERNAME_TAKEN, status=400)
    if code == "file_too_large":
        raise AppError(ErrorCode.FILE_TOO_LARGE, status=400)
    if code == "invalid_format":
        raise AppError(ErrorCode.INVALID_FORMAT, status=400)
    if code == "no_changes":
        raise AppError(ErrorCode.NO_CHANGES, status=400)

    return data
