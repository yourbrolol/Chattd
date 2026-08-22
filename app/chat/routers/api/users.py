from fastapi import Depends, HTTPException
from app.core.router import APIRouter
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.users import UserProfileResponse
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