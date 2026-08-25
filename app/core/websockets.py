import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.core.router import APIRouter
from jose import jwt, JWTError
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.core.auth import get_current_ws_user, SECRET_KEY, ALGORITHM
from app.chat.models import User
from app.chat.services.rooms import (
    get_room,
    user_is_room_member,
    WS_CLOSE_AUTH_REQUIRED,
    WS_CLOSE_FORBIDDEN,
    WS_CLOSE_NOT_FOUND
)
from app.chat.services.messages import add_message, retrieve_messages
from app.core.ws_ratelimit import SlidingWindowLimiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])

ws_connect_limiter = SlidingWindowLimiter(max_events=3, per_seconds=3)
ws_message_limiter = SlidingWindowLimiter(max_events=1, per_seconds=1)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if room_name not in self.active_connections:
            self.active_connections[room_name] = set()
        self.active_connections[room_name].add(websocket)

    def disconnect(self, websocket: WebSocket, room_name: str):
        if room_name in self.active_connections:
            self.active_connections[room_name].discard(websocket)
            if not self.active_connections[room_name]:
                del self.active_connections[room_name]

    async def broadcast_to_room(self, room_name: str, message_dict: dict):
        if room_name in self.active_connections:
            dead_sockets = []
            for connection in self.active_connections[room_name]:
                try:
                    await connection.send_text(json.dumps(message_dict))
                except Exception:
                    dead_sockets.append(connection)
            for ws in dead_sockets:
                self.disconnect(ws, room_name)

manager = ConnectionManager()

async def get_user_from_token(token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        async with SessionLocal() as db:
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            return result.scalars().first()
    except JWTError:
        return None

@router.websocket("/ws/chat/{room_name}/")
async def websocket_endpoint(
    websocket: WebSocket,
    room_name: str,
    #user: User | None = Depends(get_current_ws_user),
):
    print("Enter websocket.")
    user = websocket.user
    if not user.is_authenticated:
        await websocket.close(code=WS_CLOSE_AUTH_REQUIRED)
        return

    connect_key = f"ws-connect:{user.username}"
    if not ws_connect_limiter.allow(connect_key):
        logger.warning("connect: rate limit exceeded for %s", user.username)
        status = ws_connect_limiter.status(connect_key)
        await websocket.close(code=4029, reason="rate_limited")
        return

    async with SessionLocal() as db:
        room = await get_room(db, room_name)
        if not room:
            await websocket.close(code=WS_CLOSE_NOT_FOUND)
            return
            
        if not await user_is_room_member(db, room, user):
            logger.warning("connect: user %s is not a member of %s", user.username, room_name)
            await websocket.close(code=WS_CLOSE_FORBIDDEN)
            return

        messages = await retrieve_messages(db, room)
        message_history = []
        for msg in messages:
            sender_stmt = select(User).where(User.id == msg.user_id)
            res = await db.execute(sender_stmt)
            sender = res.scalars().first()
            message_history.append({
                "user": sender.username if sender else "[Deleted User]",
                "content": msg.content,
                "avatar": f"/media/{sender.avatar}" if sender and sender.avatar else None
            })

    await manager.connect(websocket, room_name)
    
    await websocket.send_text(json.dumps({
        "type": "init",
        "message_history": message_history
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
            except json.JSONDecodeError:
                continue
                
            msg_type = msg_data.get("type")
            if msg_type == "chat_message":
                msg_key = f"ws-msg:{user.username}"
                if not ws_message_limiter.allow(msg_key):
                    logger.warning("send: rate limit exceeded for %s", user.username)
                    status = ws_message_limiter.status(msg_key)
                    await websocket.send_text(json.dumps({
                        "type": "rate_limited",
                        "detail": "rate_limit_exceeded",
                        "limit": status["limit"],
                        "remaining": status["remaining"],
                        "retry_after": status["reset"],
                    }))
                    continue
                content = msg_data.get("message", "")
                async with SessionLocal() as db:
                    saved_msg = await add_message(db, room_name, user.id, content)
                    if saved_msg:
                        avatar_url = f"/media/{user.avatar}" if user.avatar else None
                        await manager.broadcast_to_room(room_name, {
                            "type": "chat_message",
                            "user": user.username,
                            "content": saved_msg.content,
                            "avatar": avatar_url
                        })
                        status = ws_message_limiter.status(msg_key)
                        await websocket.send_text(json.dumps({
                            "type": "quota_left",
                            "limit": status["limit"],
                            "remaining": status["remaining"],
                            "retry_after": status["reset"],
                        }))
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
