import logging

from django.db import IntegrityError
from channels.db import database_sync_to_async
from chat.models import ChatRoom

logger = logging.getLogger(__name__)

async def create_room(room_name, owner, room_type):
    if not room_name or room_name == '':
        return None
    try:
        room = await database_sync_to_async(lambda: ChatRoom.objects.create(name=room_name, owner=owner, room_type=room_type))()
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