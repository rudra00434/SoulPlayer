import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ListeningRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'listening_room_{self.room_code}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Announce arrival
        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': 'System',
                    'message': f"{self.user.username} joined the jam!"
                }
            )

    async def disconnect(self, close_code):
        # Announce departure
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': 'System',
                    'message': f"{self.user.username} left the jam."
                }
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket (Frontend Javascript)
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']
        
        if action == 'chat':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': self.user.username if self.user.is_authenticated else 'Guest',
                    'message': data['message'],
                }
            )
            return

        timestamp = data.get('timestamp', 0)
        song_id = data.get('song_id', None)

        # Broadcast the message to everyone else in the Redis group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'play_song',
                'action': action,
                'timestamp': timestamp,
                'song_id': song_id,
            }
        )

    # Receive message from Redis group and send to single WebSocket
    async def play_song(self, event):
        action = event['action']
        timestamp = event['timestamp']
        song_id = event.get('song_id', None)

        # Send actual message to the Javascript frontend
        await self.send(text_data=json.dumps({
            'action': action,
            'timestamp': timestamp,
            'song_id': song_id,
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'chat',
            'username': event['username'],
            'message': event['message'],
        }))
        
class PlaylistConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.playlist_id = self.scope['url_route']['kwargs']['playlist_id']
        self.group_name = f'playlist_{self.playlist_id}'
        self.user = self.scope['user']
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.group_name,
                {'type': 'presence_update', 'username': self.user.username, 'action': 'viewing'}
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.group_name,
                {'type': 'presence_update', 'username': self.user.username, 'action': 'left'}
            )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def song_added(self, event):
        await self.send(text_data=json.dumps({
            'type': 'song_added', 'song_id': event['song_id'],
            'song_title': event['song_title'], 'song_artist': event['song_artist'],
            'song_image': event['song_image'], 'song_duration': event['song_duration'],
            'added_by': event['added_by'],
        }))

    async def collaborator_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'collaborator_joined', 'username': event['username'], 'user_id': event['user_id'],
        }))

    async def collaborator_removed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'collaborator_removed', 'user_id': event['user_id'],
        }))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence', 'username': event['username'], 'action': event['action'],
        }))
