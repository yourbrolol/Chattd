import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .models import ChatMessage, ChatRoom

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

        room = await database_sync_to_async(
            lambda: ChatRoom.objects.get_or_create(name=self.room_name)[0]
        )()

        messages = await database_sync_to_async(
            lambda: list(
                ChatMessage.objects
                .filter(room=room)
                .order_by("timestamp")
                .values_list("content", flat=True)
            )
        )()

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'message_history': messages
        }))

        logger.info(f"consumers.py: connect(): sent {messages}")

    async def disconnect(self, close_code):
        logger.info("consumers.py: disconnect()")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return  # ignore empty messages

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {text_data}")
            return

        message_type = data.get('type')  # <-- safe access
        if not message_type:
            logger.warning(f"Received message without type: {data}")
            return

        # if message_type == 'get_history':
        #     await self.send(text_data=json.dumps({
        #         'type': 'init',
        #         'message_history': message_history
        #     }))
        if message_type == 'chat_message':
            message = data.get('message', '')
            logger.info(f"consumers.py: receive(): {message}")

            room = await database_sync_to_async(
                lambda: ChatRoom.objects.get_or_create(name=self.room_name)[0]
            )()

            await database_sync_to_async(lambda: ChatMessage.objects.create(
                room = room,
                content = message
            ))()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message
                }
            )
        
    async def chat_message(self, event):
        message = event['message']
        logger.info(f"consumers.py: chat_message(): {message}")

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))