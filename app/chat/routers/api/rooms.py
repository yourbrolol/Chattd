import logging

from fastapi import Depends, status
from app.core.router import APIRouter
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
from app.chat.errors import AppError, ErrorCode

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
        raise AppError(ErrorCode.EMPTY_NAME, status=400)
    if code == rooms_service.ROOM_EXISTS:
        raise AppError(ErrorCode.NAME_TAKEN, status=400)
    if not room:
        raise AppError(ErrorCode.CREATE_FAILED, status=400)
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
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if status_code == rooms_service.ROOM_FORBIDDEN:
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    if status_code == rooms_service.ROOM_NOT_MEMBER:
        raise AppError(ErrorCode.NOT_MEMBER, status=403)
    return data

@router.post("/{room_name}/leave")
async def leave_room(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, code = await rooms_service.leave_room(db, room_name, current_user)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if code == rooms_service.ROOM_NOT_MEMBER:
        raise AppError(ErrorCode.NOT_MEMBER, status=403)
    return {"message": "left_room"}

@router.delete("/{room_name}/delete")
async def delete_room(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, code = await rooms_service.delete_room_entry(db, room_name, current_user)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if code == rooms_service.ROOM_FORBIDDEN:
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    return {"message": "room_deleted"}

@router.post("/join")
async def join_room(
    join_data: JoinRoom,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room, status_code = await rooms_service.join_room(db, join_data.room_name, current_user)

    if status_code == rooms_service.JOIN_AUTH_REQUIRED:
        raise AppError(ErrorCode.AUTH_REQUIRED, status=401)
    if status_code == rooms_service.JOIN_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if status_code == rooms_service.JOIN_FORBIDDEN:
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    if status_code == rooms_service.APPLICATION_REQUIRED:
        raise AppError(ErrorCode.APP_REQUIRED, status=403)
    if status_code == rooms_service.APPLICATION_PENDING:
        raise AppError(ErrorCode.APP_PENDING, status=403)

    return {
        "name": room.name,
        "room_type": room.type.value,
        "joined": status_code in (rooms_service.JOIN_OK, rooms_service.JOIN_ALREADY_MEMBER),
        "already_member": status_code == rooms_service.JOIN_ALREADY_MEMBER,
    }

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
        raise AppError(ErrorCode.EMPTY_NAME, status=400)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if code == rooms_service.ROOM_FORBIDDEN:
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    if code == rooms_service.ROOM_EXISTS:
        raise AppError(ErrorCode.NAME_TAKEN, status=400)
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
        raise AppError(ErrorCode.EMPTY_USERNAME, status=400)
    if code == rooms_service.ROOM_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if code == rooms_service.ROOM_FORBIDDEN:
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    if code == rooms_service.ROOM_MEMBER_NOT_FOUND:
        raise AppError(ErrorCode.USER_NOT_MEMBER, status=404)
    return {"message": "member_kicked"}
