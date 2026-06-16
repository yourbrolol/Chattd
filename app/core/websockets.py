import json
import logging
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.core.auth import SECRET_KEY, ALGORITHM
from app.chat.models import User
from app.chat.services.rooms import (
    get_room,
    user_is_room_member,
    WS_CLOSE_AUTH_REQUIRED,
    WS_CLOSE_FORBIDDEN,
    WS_CLOSE_NOT_FOUND
)
from app.chat.services.messages import add_message, retrieve_messages

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])

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

@router.websocket("/ws/chat/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_name: str,
    token: Optional[str] = Query(None)
):
    if not token:
        await websocket.close(code=WS_CLOSE_AUTH_REQUIRED)
        return
        
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=WS_CLOSE_AUTH_REQUIRED)
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
                "user": sender.username if sender else "(deleted user)",
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
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
