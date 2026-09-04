from fastapi import Depends, status
from app.core.router import APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.chat.schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse
from app.chat.services import auth as auth_service
from app.chat.errors import AppError, ErrorCode

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user, code = await auth_service.register_user(db, user_data)
    if code == auth_service.AUTH_USERNAME_TAKEN:
        raise AppError(ErrorCode.USERNAME_TAKEN, status=400)
    if code == auth_service.AUTH_BAD_REQUEST:
        raise AppError(ErrorCode.BAD_REQUEST, status=422)
    if not new_user:
        raise AppError(ErrorCode.CREATE_FAILED, status=400)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    token_payload, code = await auth_service.login_user(db, user_data)
    if code == auth_service.AUTH_INVALID_CREDENTIALS:
        raise AppError(ErrorCode.INVALID_CREDENTIALS, status=400)
    if code == auth_service.AUTH_BAD_REQUEST:
        raise AppError(ErrorCode.BAD_REQUEST, status=422)
    return token_payload

@router.post("/logout")
async def logout():
    redirect_response = RedirectResponse(url="/login", status_code=303)

    redirect_response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
        #secure=True
    )

    return redirect_response
