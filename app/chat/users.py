from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from app.chat.schemas.users import UserProfileResponse, SettingsEditResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: int):
    pass

@router.post("/settings", response_model=SettingsEditResponse)
async def edit_settings(
    username: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None)
):
    pass
