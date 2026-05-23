import logging

from channels.db import database_sync_to_async
from chat.models import ChatMessage

from .rooms import get_room

logger = logging.getLogger(__name__)

async def add_message(room_name, user, msg):
    if not msg or msg == '': return None

    user_obj = await database_sync_to_async(lambda: user)()
    room = await get_room(room_name)
    if room == None: return
    message = await database_sync_to_async(lambda: ChatMessage.objects.create(
        room=room,
        user=user_obj,
        content=msg
    ))()

    logger.info(f"messages.py: add_message(): {msg}")

    return message

async def retrieve_messages(room, order, values):
    messages = await database_sync_to_async(
        lambda: list(
            ChatMessage.objects
            .filter(room=room)
            .order_by(order)
            .values(*values)
        )
    )()
    return messages