from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.chat.schemas.rooms import (
    RoomCreate,
    RoomSearch,
    JoinRoom,
    EditRoom,
    KickRoomMember,
    RoomListItem,
    RoomDetailsResponse
)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(room_data: RoomCreate):
    pass

@router.get("/search")
async def search_rooms(q: str):
    pass

@router.get("", response_model=List[RoomListItem])
async def list_rooms():
    pass

@router.get("/{room_name}", response_model=RoomDetailsResponse)
async def room_details(room_name: str):
    pass

@router.post("/{room_name}/leave")
async def leave_room(room_name: str):
    pass

@router.delete("/{room_name}")
async def delete_room(room_name: str):
    pass

@router.post("/join")
async def join_room(join_data: JoinRoom):
    pass

@router.patch("/{room_name}")
async def edit_room(room_name: str, edit_data: EditRoom):
    pass

@router.post("/{room_name}/kick")
async def kick_member(room_name: str, kick_data: KickRoomMember):
    pass
