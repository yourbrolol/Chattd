from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.chat.models import ChatRoom, RoomApplication, User

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
    return getattr(app, "status") if app else None

async def can_join_room(
    db: AsyncSession, room: ChatRoom, user: User
) -> bool:
    if room.type in (ChatRoom.RoomType.PUBLIC, ChatRoom.RoomType.UNLISTED): return True
    # TODO: add private room support
    return False