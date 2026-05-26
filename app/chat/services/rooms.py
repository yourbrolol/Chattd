import logging

from django.db import IntegrityError
from channels.db import database_sync_to_async
from chat.models import ChatRoom, RoomMembership, RoomApplication

logger = logging.getLogger(__name__)

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


def get_app_status(room, user):
    """Return latest application status for a user in a room, or None."""
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    app = (
        room.applications.filter(applicant=user)
        .order_by("-created_at")
        .first()
    )
    return app.status if app is not None else None


def can_join_room(room, user):
    """
    Whether a user is allowed to join the room right now.

    - PUBLIC / UNLISTED: anyone can join.
    - PRIVATE: user must have an APPROVED application.
    """
    if room.room_type in (
        ChatRoom.RoomTypes.PUBLIC,
        ChatRoom.RoomTypes.UNLISTED,
    ):
        return True

    if room.room_type == ChatRoom.RoomTypes.PRIVATE:
        return get_app_status(room, user) == RoomApplication.Status.APPROVED

    return False


def is_room_member(room, user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    user_id = getattr(user, 'pk', None)
    if not user_id:
        return False
    room_id = room.pk if hasattr(room, 'pk') else room
    return RoomMembership.objects.filter(room_id=room_id, user_id=user_id).exists()


def create_app(room, user):
    """Create a new application for a room."""
    return RoomApplication.objects.create(
        applicant=user,
        room=room
    )


def join_room_sync(room_name, user):
    if user is None or not user.is_authenticated:
        return None, JOIN_AUTH_REQUIRED

    room_name = (room_name or '').strip()
    if not room_name:
        return None, JOIN_NOT_FOUND

    try:
        room = ChatRoom.objects.get(name=room_name)
    except ChatRoom.DoesNotExist:
        return None, JOIN_NOT_FOUND

    if is_room_member(room, user):
        return room, JOIN_ALREADY_MEMBER

    app_status = get_app_status(room, user)

    if not can_join_room(room, user):
        if room.room_type == ChatRoom.RoomTypes.PRIVATE:
            if app_status is None:
                return None, APPLICATION_REQUIRED
            if app_status == RoomApplication.Status.REJECTED:
                return None, JOIN_FORBIDDEN
            if app_status == RoomApplication.Status.PENDING:
                return None, APPLICATION_PENDING
        return None, JOIN_FORBIDDEN

    RoomMembership.objects.create(
        room=room,
        user=user,
        role=RoomMembership.Role.MEMBER,
    )
    return room, JOIN_OK

def _create_room_sync(room_name, owner, room_type):
    room = ChatRoom.objects.create(name=room_name, owner=owner, room_type=room_type)
    if owner is not None:
        RoomMembership.objects.create(
            room=room,
            user=owner,
            role=RoomMembership.Role.OWNER,
        )
    return room

async def create_room(room_name, owner, room_type):
    if not room_name or room_name == '':
        return None
    try:
        room = await database_sync_to_async(_create_room_sync)(room_name, owner, room_type)
    except IntegrityError:
        return None
    return room

async def get_room(room_name):
    if not room_name or room_name == '':
        return None
    try:
        room = await database_sync_to_async(lambda: ChatRoom.objects.get(name=room_name))()
    except ChatRoom.DoesNotExist:
        logger.info("get_room: no room found for %s", room_name)
        return None
    return room

async def join_room(room_name, user):
    return await database_sync_to_async(join_room_sync)(room_name, user)

async def user_is_room_member(room, user):
    return await database_sync_to_async(is_room_member)(room, user)