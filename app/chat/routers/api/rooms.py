import logging

from fastapi import Depends, HTTPException, status
from app.core.router import APIRouter
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User
from app.chat.schemas.rooms import (
    RoomCreate,
    JoinRoom,
    EditRoom,
    KickRoomMember,
    RoomListItem,
    RoomDetailsResponse
)
from app.chat.services import rooms as rooms_service

router = APIRouter(prefix="/rooms", tags=["rooms"])

logger = logging.getLogger(__name__)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room, code = await rooms_service.create_room_entry(db, room_data.room_name, current_user, room_data.room_type)
    if code == rooms_service.ROOM_EMPTY_NAME:
        raise HTTPException(status_code=400, detail="Room name cannot be empty.")
    if code == rooms_service.ROOM_EXISTS:
        raise HTTPException(status_code=400, detail="Room already exists.")
    if not room:
        raise HTTPException(status_code=400, detail="Failed to create room.")
    return {"message": "Room created successfully", "name": room.name}

@router.get("/search")
async def search_rooms(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await rooms_service.search_rooms_data(db, current_user, q)

@router.get("", response_model=List[RoomListItem])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await rooms_service.list_rooms_data(db, current_user)

@router.get("/{room_name}", response_model=RoomDetailsResponse)
async def room_details(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data, status_code = await rooms_service.get_room_details(db, room_name, current_user)
    if status_code == rooms_service.ROOM_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if status_code == rooms_service.ROOM_FORBIDDEN:
        raise HTTPException(status_code=403, detail="forbidden")
    if status_code == rooms_service.ROOM_NOT_MEMBER:
        raise HTTPException(status_code=403, detail="not_member")
    return data

@router.post("/{room_name}/leave")
async def leave_room(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, code = await rooms_service.leave_room(db, room_name, current_user)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if code == rooms_service.ROOM_NOT_MEMBER:
        raise HTTPException(status_code=403, detail="not_member")
    return {"message": "left_room"}

@router.delete("/{room_name}/delete")
async def delete_room(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, code = await rooms_service.delete_room_entry(db, room_name, current_user)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if code == rooms_service.ROOM_FORBIDDEN:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"message": "room_deleted"}

@router.post("/join", response_class=JSONResponse)
async def join_room(
    join_data: JoinRoom,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room, status_code = await rooms_service.join_room(db, join_data.room_name, current_user)
    
    if status_code == rooms_service.JOIN_AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="auth_required")
    if status_code == rooms_service.JOIN_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if status_code == rooms_service.JOIN_FORBIDDEN:
        raise HTTPException(status_code=403, detail="forbidden")
    if status_code == rooms_service.APPLICATION_REQUIRED:
        return JSONResponse(status_code=403, content={"warning": "app_required"})
    if status_code == rooms_service.APPLICATION_PENDING:
        return JSONResponse(status_code=403, content={"warning": "app_pending"})
    
    return JSONResponse(content={
        "name": room.name,
        "room_type": room.type.value,
        "joined": status_code in (rooms_service.JOIN_OK, rooms_service.JOIN_ALREADY_MEMBER),
        "already_member": status_code == rooms_service.JOIN_ALREADY_MEMBER,
    })

@router.patch("/{room_name}")
async def edit_room(
    room_name: str,
    edit_data: EditRoom,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_name = edit_data.name.strip()
    data, code = await rooms_service.edit_room_entry(db, room_name, new_name, current_user)
    if code == rooms_service.ROOM_EMPTY_NAME:
        raise HTTPException(status_code=400, detail="empty_name")
    if code == rooms_service.ROOM_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if code == rooms_service.ROOM_FORBIDDEN:
        raise HTTPException(status_code=403, detail="forbidden")
    if code == rooms_service.ROOM_EXISTS:
        raise HTTPException(status_code=400, detail="name_taken")
    return data

@router.post("/{room_name}/kick")
async def kick_member(
    room_name: str,
    kick_data: KickRoomMember,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    username_to_kick = kick_data.username.strip()
    success, code = await rooms_service.kick_member(db, room_name, username_to_kick, current_user)
    if code == rooms_service.ROOM_EMPTY_NAME:
        raise HTTPException(status_code=400, detail="empty_username")
    if code == rooms_service.ROOM_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if code == rooms_service.ROOM_FORBIDDEN:
        raise HTTPException(status_code=403, detail="forbidden")
    if code == rooms_service.ROOM_MEMBER_NOT_FOUND:
        raise HTTPException(status_code=404, detail="user_not_member")
    return {"message": "member_kicked"}
