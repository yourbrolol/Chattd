from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import ChatMessage, ChatRoom, User, RoomMembership

async def add_message(
    db: AsyncSession, room_name: str, user_id: int, msg: str
) -> ChatMessage | None:
    if not (msg or '').strip(): return None
    room_stmt = select(ChatRoom).where(ChatRoom.name == room_name)
    user_stmt = select(User).where(User.id == user_id)
    room_result = await db.execute(room_stmt)
    room = room_result.scalars().first()
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()

    if not room or not user: return None

    membership_stmt = select(RoomMembership).where(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == user.id
    )
    membership_result = await db.execute(membership_stmt)
    if not membership_result.scalars().first(): return None

    try:
        chat_message = ChatMessage(room_id=room.id, user_id=user.id, content=msg)
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        return chat_message
    except Exception:
        return None

async def retrieve_messages(
    db: AsyncSession, room: ChatRoom
) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.room_id == room.id)
        .order_by(ChatMessage.timestamp.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())