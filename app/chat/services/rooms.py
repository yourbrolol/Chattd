from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Tuple, Optional

from app.chat.models import ChatRoom, RoomApplication, User, RoomMembership

JOIN_OK = 'ok'
JOIN_ALREADY_MEMBER = 'already_member'
JOIN_NOT_FOUND = 'not_found'
JOIN_FORBIDDEN = 'forbidden'
JOIN_AUTH_REQUIRED = 'auth_required'
APPLICATION_REQUIRED = 'app_required'
APPLICATION_PENDING = 'app_pending'

WS_CLOSE_AUTH_REQUIRED = 4001
WS_CLOSE_FORBIDDEN = 4003
WS_CLOSE_NOT_FOUND = 4004

ROOM_OK = "ok"
ROOM_NOT_FOUND = "not_found"
ROOM_FORBIDDEN = "forbidden"
ROOM_NOT_MEMBER = "not_member"

async def get_app_status(
    db: AsyncSession, room: ChatRoom, user: User
) -> str | None:
    if user is None or room is None:
        return None
    stmt = select(RoomApplication).where(
        RoomApplication.room_id == room.id,
        RoomApplication.applicant_id == user.id
    )
    result = await db.execute(stmt)
    app = result.scalars().first()
    return app.status.value if app else None

async def can_join_room(
    db: AsyncSession, room: ChatRoom, user: User
) -> bool:
    if room.type in (ChatRoom.RoomType.PUBLIC, ChatRoom.RoomType.UNLISTED):
        return True
    if room.type == ChatRoom.RoomType.PRIVATE:
        status = await get_app_status(db, room, user)
        return status == RoomApplication.ApplicationStatus.APPROVED
    return False

async def is_room_member(db: AsyncSession, room_id: int, user_id: int) -> bool:
    stmt = select(RoomMembership).where(
        RoomMembership.room_id == room_id,
        RoomMembership.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None

async def user_is_room_member(db: AsyncSession, room: ChatRoom, user: User) -> bool:
    if not user or not room:
        return False
    return await is_room_member(db, room.id, user.id)

async def get_room(db: AsyncSession, room_name: str) -> Optional[ChatRoom]:
    if not room_name:
        return None
    stmt = select(ChatRoom).where(ChatRoom.name == room_name)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_room(db: AsyncSession, room_name: str, owner: User, room_type: str) -> Optional[ChatRoom]:
    if not room_name:
        return None
    try:
        room = ChatRoom(
            name=room_name,
            owner_id=owner.id if owner else None,
            type=ChatRoom.RoomType(room_type)
        )
        db.add(room)
        await db.flush()  # Populates room.id

        if owner:
            membership = RoomMembership(
                room_id=room.id,
                user_id=owner.id,
                role=RoomMembership.Role.OWNER
            )
            db.add(membership)

        await db.commit()
        await db.refresh(room)
        return room
    except Exception:
        await db.rollback()
        return None

async def join_room(db: AsyncSession, room_name: str, user: User) -> Tuple[Optional[ChatRoom], str]:
    if not user:
        return None, JOIN_AUTH_REQUIRED
    room_name = (room_name or "").strip()
    if not room_name:
        return None, JOIN_NOT_FOUND

    room = await get_room(db, room_name)
    if not room:
        return None, JOIN_NOT_FOUND

    if await is_room_member(db, room.id, user.id):
        return room, JOIN_ALREADY_MEMBER

    allowed = await can_join_room(db, room, user)
    if not allowed:
        if room.type == ChatRoom.RoomType.PRIVATE:
            app_status = await get_app_status(db, room, user)
            if app_status is None:
                return None, APPLICATION_REQUIRED
            if app_status == RoomApplication.ApplicationStatus.REJECTED:
                return None, JOIN_FORBIDDEN
            if app_status == RoomApplication.ApplicationStatus.PENDING:
                return None, APPLICATION_PENDING
        return None, JOIN_FORBIDDEN

    membership = RoomMembership(
        room_id=room.id,
        user_id=user.id,
        role=RoomMembership.Role.MEMBER
    )
    db.add(membership)
    await db.commit()
    return room, JOIN_OK

async def get_room_details(db: AsyncSession, room_name: str, user: User) -> Tuple[Optional[dict], str]:
    stmt = (
        select(ChatRoom)
        .where(ChatRoom.name == room_name)
        .options(selectinload(ChatRoom.owner))
    )
    result = await db.execute(stmt)
    room = result.scalars().first()
    if not room:
        return None, ROOM_NOT_FOUND

    is_member = await is_room_member(db, room.id, user.id)

    if room.type == ChatRoom.RoomType.PRIVATE and not is_member:
        return None, ROOM_FORBIDDEN

    if not is_member:
        return None, ROOM_NOT_MEMBER

    # Fetch memberships and users
    mem_stmt = (
        select(RoomMembership)
        .where(RoomMembership.room_id == room.id)
        .options(selectinload(RoomMembership.user))
    )
    mem_result = await db.execute(mem_stmt)
    memberships = mem_result.scalars().all()

    members_list = []
    for membership in memberships:
        u = membership.user
        avatar_url = f"/media/{u.avatar}" if u and u.avatar else None

        members_list.append({
            "id": u.id if u else None,
            "username": u.username if u else "(deleted user)",
            "role": membership.role,
            "avatar": avatar_url,
        })

    data = {
        "id": room.id,
        "name": room.name,
        "room_type": room.type.value,
        "owner": room.owner.username if room.owner else None,
        "members_data": members_list,
    }
    return data, ROOM_OK