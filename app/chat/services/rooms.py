import logging

from django.db import IntegrityError
from channels.db import database_sync_to_async
from chat.models import ChatRoom, RoomMembership

logger = logging.getLogger(__name__)

JOIN_OK = 'ok'
JOIN_ALREADY_MEMBER = 'already_member'
JOIN_NOT_FOUND = 'not_found'
JOIN_FORBIDDEN = 'forbidden'
JOIN_AUTH_REQUIRED = 'auth_required'

WS_CLOSE_AUTH_REQUIRED = 4001
WS_CLOSE_FORBIDDEN = 4003
WS_CLOSE_NOT_FOUND = 4004


def can_join_room(room):
    """Whether new users may self-join (public/unlisted only for now)."""
    return room.room_type in (
        ChatRoom.RoomTypes.PUBLIC,
        ChatRoom.RoomTypes.UNLISTED,
    )


def is_room_member(room, user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    user_id = getattr(user, 'pk', None)
    if not user_id:
        return False
    room_id = room.pk if hasattr(room, 'pk') else room
    return RoomMembership.objects.filter(room_id=room_id, user_id=user_id).exists()


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

    if not can_join_room(room):
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