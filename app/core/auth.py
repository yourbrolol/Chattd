from datetime import datetime, timedelta, timezone
import json
import logging
from starlette.authentication import AuthenticationBackend, AuthCredentials, AuthenticationError, UnauthenticatedUser
from typing import Optional
from fastapi import Depends, Request, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

from app.core.database import get_db, SessionLocal
from app.chat.models import User

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

logger = logging.getLogger(__name__)

async def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")

    if token is None:
        logger.error("No token found in cookies")
        from app.chat.errors import AppError, ErrorCode
        raise AppError(ErrorCode.AUTH_REQUIRED, status=401)

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

async def parse_token(token: str):
    """Normalize either a raw JWT string or a serialized auth payload into a dict."""
    if token is None:
        return {}
    if isinstance(token, dict):
        return token

    # Raw JWT strings are not JSON; only attempt to unwrap serialized payloads.
    if isinstance(token, str):
        parts = token.split(".")
        if len(parts) == 3:
            return token

        cleaned = token.replace("\'", "\"")
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed.get('access_token')
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    return None

async def authenticate_token(token: str, db: AsyncSession) -> User | UnauthenticatedUser:
    try:
        access_token = await parse_token(token=token)
        print("token", access_token)
        if isinstance(access_token, dict):
            access_token = access_token.get("access_token")
        if access_token is None: return UnauthenticatedUser()
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded JWT payload: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None: return UnauthenticatedUser()
    except JWTError as e:
        logger.error(f"Error decoding JWT token {token}, exception: {e}")
        raise AuthenticationError("Error decoding JWT token.")
    stmt = select(User).where(User.id == user_id)
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
            print("Token:", token, "Type:", type(token))
            
            if token is None: return AuthCredentials([]), UnauthenticatedUser()

            async with SessionLocal() as db: user = await authenticate_token(token, db)
            
            if isinstance(user, UnauthenticatedUser): return AuthCredentials([]), UnauthenticatedUser()

            print("User:", user)

            return AuthCredentials(["authenticated"]), user

        except Exception:
            logger.exception("Authentication backend failed")
            raise
