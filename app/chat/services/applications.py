import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.chat.models import ChatRoom, RoomMembership, RoomApplication, User

logger = logging.getLogger(__name__)

APP_OK = "ok"
APP_ALREADY_MEMBER = "already_member"
APP_NOT_FOUND = "not_found"
APP_AUTH_REQUIRED = "auth_required"
APP_ALREADY_PENDING = "already_pending"
APP_ALREADY_APPROVED = "already_approved"

async def apply_to_room(
    db: AsyncSession, room_name: str, user: User
) -> Tuple[Optional[RoomApplication], str]:
    if user is None:
        return None, APP_AUTH_REQUIRED

    room_name = (room_name or "").strip()
    if not room_name:
        return None, APP_NOT_FOUND

    stmt = select(ChatRoom).where(ChatRoom.name == room_name)
    result = await db.execute(stmt)
    room = result.scalars().first()
    if not room:
        return None, APP_NOT_FOUND

    member_stmt = select(RoomMembership).where(
        RoomMembership.room_id == room.id, RoomMembership.user_id == user.id
    )
    member_result = await db.execute(member_stmt)
    if member_result.scalars().first():
        return None, APP_ALREADY_MEMBER

    app_stmt = select(RoomApplication).where(
        RoomApplication.room_id == room.id, RoomApplication.applicant_id == user.id
    ).with_for_update()
    app_result = await db.execute(app_stmt)
    app = app_result.scalars().first()

    if not app:
        app = RoomApplication(
            applicant_id=user.id,
            room_id=room.id,
            status="PENDING",
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)
        return app, APP_OK

    if app.status == "APPROVED":
        return app, APP_ALREADY_APPROVED
    if app.status == "PENDING":
        return app, APP_ALREADY_PENDING

    if app.status == "REJECTED":
        app.status = "PENDING"
        await db.commit()
        await db.refresh(app)

    return app, APP_OK

async def review_application(
    db: AsyncSession,
    application_id: int,
    acting_user: User,
    approve: bool,
    auto_create_membership=True,
) -> Tuple[Optional[RoomApplication], Optional[str]]:
    stmt = select(RoomApplication).where(RoomApplication.id == application_id)
    result = await db.execute(stmt)
    app = result.scalars().first()
    if not app:
        return None, None, APP_NOT_FOUND

    room_stmt = select(ChatRoom).where(ChatRoom.id == app.room_id)
    room_result = await db.execute(room_stmt)
    room = room_result.scalars().first()
    if not room or getattr(room, "owner_id") != acting_user.id:
        return None, None, "forbidden"

    new_status = "APPROVED" if approve else "REJECTED"
    if app.status == new_status:
        return app, room.name, None

    app.status = new_status

    if auto_create_membership and approve:
        mem_stmt = select(RoomMembership).where(
            RoomMembership.room_id == app.room_id, RoomMembership.user_id == app.applicant_id
        )
        mem_result = await db.execute(mem_stmt)
        if not mem_result.scalars().first():
            membership = RoomMembership(user_id=app.applicant_id, room_id=app.room_id)
            db.add(membership)
    
    await db.commit()
    await db.refresh(app)
    return app, room.name, None


async def get_pending_applications_for_owner(db: AsyncSession, current_user: User) -> list[dict]:
    stmt = (
        select(RoomApplication)
        .join(ChatRoom)
        .options(selectinload(RoomApplication.applicant), selectinload(RoomApplication.room))
        .where(ChatRoom.owner_id == current_user.id, RoomApplication.status == RoomApplication.ApplicationStatus.PENDING)
        .order_by(RoomApplication.created_at.asc())
    )
    result = await db.execute(stmt)
    apps = result.scalars().all()
    return [
        {
            "id": a.id,
            "room": a.room.name,
            "applicant": a.applicant.username if a.applicant else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]


async def get_pending_applications_for_room(db: AsyncSession, room_name: str, current_user: User) -> Tuple[Optional[list[dict]], Optional[str]]:
    room_stmt = select(ChatRoom).where(ChatRoom.name == room_name)
    room_res = await db.execute(room_stmt)
    room = room_res.scalars().first()
    if not room:
        return None, "room_not_found"
    if room.owner_id != current_user.id:
        return None, "forbidden"

    stmt = (
        select(RoomApplication)
        .options(selectinload(RoomApplication.applicant))
        .where(RoomApplication.room_id == room.id, RoomApplication.status == RoomApplication.ApplicationStatus.PENDING)
        .order_by(RoomApplication.created_at.asc())
    )
    result = await db.execute(stmt)
    apps = result.scalars().all()
    return [
        {
            "id": a.id,
            "room": room.name,
            "applicant": a.applicant.username if a.applicant else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ], None
