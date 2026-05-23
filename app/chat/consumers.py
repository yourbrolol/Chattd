import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ChatMessage, ChatRoom
from .services.messages import add_message, retrieve_messages
from .services.rooms import get_room

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):
        logger.info("consumers.py: connect()")
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        room = get_room(self.room_name)
        if room == None: self.disconnect()

        messages = retrieve_messages(room, "timestamp", ["user__username", "content"])

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'message_history': [
                {"user": msg["user__username"], "content": msg["content"]} for msg in messages
            ]
        }))

        logger.info(f"consumers.py: connect(): sent {messages}")

    async def disconnect(self, close_code):
        logger.info("consumers.py: disconnect()")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data: return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {text_data}")
            return
        
        user = self.scope["user"]

        if not user.is_authenticated:
            logger.warning("Unauthenticated user tried to send a message!")
            return

        message_type = data.get('type')

        if not message_type:
            logger.warning(f"Received message without type: {data}")
            return
        
        if message_type == 'chat_message':
            msg = data.get('message', '')
            logger.info(f"consumers.py: receive(): {msg}")

            message = await add_message(self.room_name, user, msg)
            if message is None: return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {"user": user.username, "content": message.content}
                }
            )
        
    async def chat_message(self, event):
        content = event['message']
        user = content['user']
        message = content['content']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user': user,
            'content': message
        }))

        logger.info(f"consumers.py: chat_message(): {user}: {message}")