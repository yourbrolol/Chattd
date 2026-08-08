from datetime import datetime, timedelta, timezone
import json
import logging
from starlette.authentication import AuthenticationBackend, AuthCredentials, AuthenticationError, UnauthenticatedUser
from typing import Optional
from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decouple import config

from app.core.database import get_db, SessionLocal
from app.chat.models import User

SECRET_KEY = config("SECRET_KEY", default="supersecretkeyforjwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440, cast=int)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

logger = logging.getLogger(__name__)

async def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")

    if token is None:
        logger.error("No token found in cookies")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    return token

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_token(token: str, db: AsyncSession) -> User | UnauthenticatedUser:
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    try:
        # Parse str to dict
        cleaned = token.replace("'", '"')
        cleaned = json.loads(cleaned)
        payload = jwt.decode(cleaned['access_token'], SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded JWT payload: {payload}")
        username: str = payload.get("sub")
        if username is None: return UnauthenticatedUser()
    except JWTError as e:
        logger.error(f"Error decoding JWT token {token}, exception: {e}")
        raise AuthenticationError("Error decoding JWT token.")
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None: return UnauthenticatedUser()
    return user

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_token_from_cookie)
) -> User | UnauthenticatedUser:
    if token is None: return UnauthenticatedUser()
    return await authenticate_token(token, db)

async def get_current_ws_user(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> User | UnauthenticatedUser:
    token = websocket.cookies.get("access_token")
    if token is None: return UnauthenticatedUser()

    return await authenticate_token(token, db)

class JWTAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        try:
            print("AUTH BACKEND")

            token = conn.cookies.get("access_token")
            print("Token:", token)
            
            if token is None: return AuthCredentials([]), UnauthenticatedUser()

            async with SessionLocal() as db: user = await authenticate_token(token, db)
            
            if user is UnauthenticatedUser(): return AuthCredentials([]), UnauthenticatedUser()

            print("User:", user)

            return AuthCredentials(["authenticated"]), user

        except Exception:
            logger.exception("Authentication backend failed")
            raise
