from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.chat.schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse
from app.chat.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user, code = await auth_service.register_user(db, user_data)
    if code == auth_service.AUTH_USERNAME_TAKEN:
        raise HTTPException(status_code=400, detail="This username is already taken.")
    if code == auth_service.AUTH_BAD_REQUEST:
        raise HTTPException(status_code=422, detail="Prohibited characters.")
    if not new_user:
        raise HTTPException(status_code=400, detail="Could not create user.")
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    token_payload, code = await auth_service.login_user(db, user_data)
    if code == auth_service.AUTH_INVALID_CREDENTIALS:
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    if code == auth_service.AUTH_BAD_REQUEST:
        raise HTTPException(status_code=422, detail="Prohibited characters.")
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