import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

message_history = []

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):
        global message_history
        logger.info("consumers.py: connect()")
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'message_history': message_history
        }))

        logger.info(f"consumers.py: connect(): sent {message_history}")

    async def disconnect(self, close_code):
        logger.info("consumers.py: disconnect()")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data = None, bytes_data = None):
        global message_history
        data = json.loads(text_data)
        message = data['message']
        logger.info(f"consumers.py: recieve(): {message}")
        message_history.append(message)

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