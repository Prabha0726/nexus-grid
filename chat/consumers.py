import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

# Track users in rooms globally (Simple in-memory for this setup)
connected_users = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Update presence
        if self.room_name not in connected_users:
            connected_users[self.room_name] = set()
        connected_users[self.room_name].add(self.user.username)

        await self.broadcast_user_list()

        # Send message history
        messages = await self.get_messages(self.room_name)
        for msg in messages:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': f"{msg['user__username']}: {msg['content']}"
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update presence
        if self.room_name in connected_users:
            if self.user.username in connected_users[self.room_name]:
                connected_users[self.room_name].remove(self.user.username)
        
        await self.broadcast_user_list()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save to DB (async)
        await self.save_message(self.user, self.room_name, message)

        # Broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f"{self.user.username}: {message}"
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def broadcast_user_list(self):
        users = list(connected_users.get(self.room_name, []))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_list_update',
                'users': users
            }
        )

    async def user_list_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': event['users']
        }))

    @database_sync_to_async
    def get_messages(self, room_name):
        return list(Message.objects.filter(room_name=room_name).order_by('timestamp').values('user__username', 'content')[:50])

    @database_sync_to_async
    def save_message(self, user, room_name, content):
        Message.objects.create(user=user, room_name=room_name, content=content)
