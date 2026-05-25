import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .services.messages import add_message, retrieve_messages
from .services.rooms import (
    WS_CLOSE_AUTH_REQUIRED,
    WS_CLOSE_FORBIDDEN,
    WS_CLOSE_NOT_FOUND,
    get_room,
    user_is_room_member,
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("consumers.py: connect()")
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=WS_CLOSE_AUTH_REQUIRED)
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        room = await get_room(self.room_name)
        if room is None:
            await self.close(code=WS_CLOSE_NOT_FOUND)
            return

        if not await user_is_room_member(room, user):
            logger.warning("connect: user %s is not a member of %s", user, self.room_name)
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        messages = await retrieve_messages(room, "timestamp", ["user__username", "content"])

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'message_history': [
                {"user": msg["user__username"], "content": msg["content"]} for msg in messages
            ],
        }))

        logger.info("consumers.py: connect(): sent %s messages", len(messages))

    async def disconnect(self, close_code):
        logger.info("consumers.py: disconnect()")
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("Received non-JSON message: %s", text_data)
            return

        user = self.scope["user"]
        if not user.is_authenticated:
            logger.warning("Unauthenticated user tried to send a message!")
            return

        message_type = data.get('type')
        if not message_type:
            logger.warning("Received message without type: %s", data)
            return

        if message_type == 'chat_message':
            msg = data.get('message', '')
            logger.info("consumers.py: receive(): %s", msg)

            message = await add_message(self.room_name, user, msg)
            if message is None:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {"user": user.username, "content": message.content},
                },
            )

    async def chat_message(self, event):
        content = event['message']
        user = content['user']
        message = content['content']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user': user,
            'content': message,
        }))

        logger.info("consumers.py: chat_message(): %s: %s", user, message)
