import unicodedata
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.chat.models import User
from app.chat.schemas.auth import UserCreate, UserLogin
from app.core.auth import create_access_token, hash_password, verify_password

AUTH_OK = "ok"
AUTH_USERNAME_TAKEN = "username_taken"
AUTH_INVALID_CREDENTIALS = "invalid_credentials"
AUTH_BAD_REQUEST = "bad_request"


async def register_user(db: AsyncSession, user_data: UserCreate) -> Tuple[Optional[User], str]:
    if any(unicodedata.category(c) == "Cc" for c in user_data.username+user_data.password):
        return None, AUTH_BAD_REQUEST
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    if result.scalars().first():
        return None, AUTH_USERNAME_TAKEN

    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user, AUTH_OK


async def login_user(db: AsyncSession, user_data: UserLogin) -> Tuple[dict, str]:
    if any(unicodedata.category(c) == "Cc" for c in user_data.username+user_data.password):
        return None, AUTH_BAD_REQUEST
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        return {}, AUTH_INVALID_CREDENTIALS

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}, AUTH_OK
