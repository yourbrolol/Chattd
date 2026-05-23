import logging

from channels.db import database_sync_to_async
from chat.models import ChatMessage, ChatRoom

from services.rooms import create_room, get_room

logger = logging.getLogger(__name__)

async def add_message(room_name, username, content):
    if not content or content == '': return None

    msg = content.get('message', '')

    if not msg: return None

    user = await database_sync_to_async(lambda: username)()
    room = get_room(room_name)
    if room == None: return
    message = await database_sync_to_async(lambda: ChatMessage.objects.create(
        room=room,
        user=user,
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