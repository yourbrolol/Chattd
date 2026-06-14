from fastapi import APIRouter, Depends, HTTPException, status
from app.chat.schemas.auth import UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    pass

@router.post("/login")
async def login(user_data: UserLogin):
    pass

@router.post("/logout")
async def logout():
    pass