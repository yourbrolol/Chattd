from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User, ChatRoom, RoomMembership
from app.chat.schemas.rooms import (
    RoomCreate,
    RoomSearch,
    JoinRoom,
    EditRoom,
    KickRoomMember,
    RoomListItem,
    RoomDetailsResponse
)
from app.chat.services import rooms as rooms_service

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not room_data.room_name.strip():
        raise HTTPException(status_code=400, detail="Room name cannot be empty.")
    
    # Check if already exists
    existing = await rooms_service.get_room(db, room_data.room_name)
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists.")

    room = await rooms_service.create_room(db, room_data.room_name, current_user, room_data.room_type)
    if not room:
        raise HTTPException(status_code=400, detail="Failed to create room.")
    return {"message": "Room created successfully", "name": room.name}

@router.get("/search")
async def search_rooms(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = q.strip()
    if not q:
        return {"public_rooms": [], "joined_rooms": []}

    joined_stmt = (
        select(ChatRoom)
        .join(RoomMembership)
        .where(RoomMembership.user_id == current_user.id, ChatRoom.name.ilike(f"%{q}%"))
        .distinct()
        .limit(10)
    )
    joined_result = await db.execute(joined_stmt)
    joined_rooms = joined_result.scalars().all()

    joined_ids_stmt = select(RoomMembership.room_id).where(RoomMembership.user_id == current_user.id)
    joined_ids_result = await db.execute(joined_ids_stmt)
    joined_ids = joined_ids_result.scalars().all()

    public_stmt = (
        select(ChatRoom)
        .where(
            ChatRoom.type == ChatRoom.RoomType.PUBLIC,
            ChatRoom.name.ilike(f"%{q}%")
        )
    )
    if joined_ids:
        public_stmt = public_stmt.where(ChatRoom.id.notin_(joined_ids))
    public_stmt = public_stmt.distinct().limit(10)

    public_result = await db.execute(public_stmt)
    public_rooms = public_result.scalars().all()

    return {
        "joined_rooms": [{"name": r.name, "is_public": r.type == ChatRoom.RoomType.PUBLIC} for r in joined_rooms],
        "public_rooms": [{"name": r.name} for r in public_rooms],
    }

@router.get("", response_model=List[RoomListItem])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(ChatRoom)
        .join(RoomMembership)
        .where(RoomMembership.user_id == current_user.id)
        .distinct()
    )
    result = await db.execute(stmt)
    rooms = result.scalars().all()
    return [{"id": r.id, "name": r.name, "room_type": r.type.value} for r in rooms]

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
    room = await rooms_service.get_room(db, room_name)
    if not room:
        raise HTTPException(status_code=404, detail="not_found")
    
    stmt = select(RoomMembership).where(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == current_user.id
    )
    result = await db.execute(stmt)
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="not_member")
    
    await db.delete(membership)
    await db.commit()
    return {"message": "left_room"}

@router.delete("/{room_name}")
async def delete_room(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = await rooms_service.get_room(db, room_name)
    if not room:
        raise HTTPException(status_code=404, detail="not_found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    
    await db.delete(room)
    await db.commit()
    return {"message": "room_deleted"}

@router.post("/join")
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
        return {"warning": "app_required"}
    if status_code == rooms_service.APPLICATION_PENDING:
        return {"warning": "app_pending"}
    
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
    if not new_name:
        raise HTTPException(status_code=400, detail="empty_name")
        
    room = await rooms_service.get_room(db, room_name)
    if not room:
        raise HTTPException(status_code=404, detail="not_found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")
        
    existing = await rooms_service.get_room(db, new_name)
    if existing and existing.id != room.id:
        raise HTTPException(status_code=400, detail="name_taken")
        
    room.name = new_name
    await db.commit()
    return {"message": "name_updated", "new_name": new_name}

@router.post("/{room_name}/kick")
async def kick_member(
    room_name: str,
    kick_data: KickRoomMember,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    username_to_kick = kick_data.username.strip()
    if not username_to_kick:
        raise HTTPException(status_code=400, detail="empty_username")
        
    room = await rooms_service.get_room(db, room_name)
    if not room:
        raise HTTPException(status_code=404, detail="not_found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")
        
    # Find user to kick
    stmt = select(User).where(User.username == username_to_kick)
    result = await db.execute(stmt)
    user_to_kick = result.scalars().first()
    if not user_to_kick:
        raise HTTPException(status_code=404, detail="user_not_member")
        
    # Check membership
    mem_stmt = select(RoomMembership).where(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == user_to_kick.id
    )
    mem_result = await db.execute(mem_stmt)
    membership = mem_result.scalars().first()
    if not membership:
        raise HTTPException(status_code=404, detail="user_not_member")
        
    await db.delete(membership)
    await db.commit()
    return {"message": "member_kicked"}
