import logging

from django.db import IntegrityError
from channels.db import database_sync_to_async
from chat.models import ChatMessage, ChatRoom, User

from .rooms import is_room_member

logger = logging.getLogger(__name__)


def add_message_sync(room_name, user_id, msg):
    if not (msg or '').strip():
        return None

    try:
        room = ChatRoom.objects.get(name=room_name)
        user = User.objects.get(pk=user_id)
    except (ChatRoom.DoesNotExist, User.DoesNotExist):
        logger.warning(
            "add_message_sync: room %r or user id %s not found",
            room_name,
            user_id,
        )
        return None

    if not is_room_member(room, user):
        logger.warning(
            "add_message_sync: user %s is not a member of %s",
            user_id,
            room_name,
        )
        return None

    try:
        return ChatMessage.objects.create(room=room, user=user, content=msg)
    except IntegrityError:
        logger.exception(
            "add_message_sync: failed to save message for user %s in %s",
            user_id,
            room_name,
        )
        return None


async def add_message(room_name, user, msg):
    if not msg or msg == '':
        return None

    if not user.is_authenticated:
        return None

    user_id = getattr(user, 'pk', None)
    if not user_id:
        return None

    return await database_sync_to_async(add_message_sync)(room_name, user_id, msg)


async def retrieve_messages(room, order, values):
    room_id = room.pk

    def _fetch():
        return list(
            ChatMessage.objects
            .filter(room_id=room_id)
            .order_by(order)
            .values(*values)
        )

    return await database_sync_to_async(_fetch)()
