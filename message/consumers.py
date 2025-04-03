import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from message.models import Message, Room
from user.models import User
from datetime import datetime

ACTIVE_USERS = {}

class GlobalNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """User connects to receive notifications from all chat rooms."""
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        print(f"User {self.user.username} connected to global notifications")

        self.user_group_name = f"user_notifications_{self.user.username}"
        print(f"User group name: {self.user_group_name}")

        # Add user to their notification group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """User disconnects from notification WebSocket."""
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def send_notification(self, event):
        """Send notification event to the client."""
        print(f"Sending notification to {self.user.username}: {event}")
        await self.send(text_data=json.dumps({"sender": event["sender"], "message": event["message"], "room": event["room"]}))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        # Check if user is part of the room
        room, seller_uid, buyer_uid = await self.get_room(self.room_name)
        if room is None:
            print(f"Room {self.room_name} does not exist")
            await self.close()
            return

        if self.user.username not in [seller_uid, buyer_uid]:
            print(f"User {self.user.username} is not part of room {self.room_name}")
            await self.close()
            return

        print(f"User {self.user.username} connected to room {self.room_name}")

        if self.room_name not in ACTIVE_USERS:
            ACTIVE_USERS[self.room_name] = set()
        ACTIVE_USERS[self.room_name].add(self.user.username)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        from .consumers import ACTIVE_USERS  # Get active users
        if self.room_name in ACTIVE_USERS:
            print(f"User {self.user.username} disconnected from room {self.room_name}")
            ACTIVE_USERS[self.room_name].discard(self.user.username)
            if not ACTIVE_USERS[self.room_name]:  # If room is empty, remove it
                del ACTIVE_USERS[self.room_name]

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        sender = data["sender"]

        current_time = datetime.now()
        await self.save_message(self.room_name, self.scope["user"].username, message, current_time)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message, "sender": sender, "timeSent": current_time}
        )

        await self.notify_users(sender, message, self.room_name)

    async def notify_users(self, sender, message, room_name):
        from .consumers import ACTIVE_USERS  # Get active users
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()

        chat_room_users, room_title = await self.get_users_and_title(room_name)
        print(f"Chat room users: {chat_room_users}, Room title: {room_title}")
        print(f"Active users in room {room_name}: {ACTIVE_USERS.get(room_name, set())}")

        for user in chat_room_users:
            if user not in ACTIVE_USERS.get(room_name, set()):  # If user is NOT in chat
                print(f"User {user} is not in chat, sending notification")
                await channel_layer.group_send(
                    f"user_notifications_{user}",
                    {
                        "type": "send_notification",
                        "sender": sender,
                        "message": message,
                        "room": room_title,
                    },
                )
    
    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({
                "message": event["message"], 
                "sender": event["sender"],
                "timeSent": event["timeSent"].strftime("%Y-%m-%d %H:%M:%S")
            })
        )

    @sync_to_async
    def get_users_and_title(self, rid):
        try:
            room = Room.objects.get(rid=rid)
            users = [room.seller.uid, room.buyer.uid]
            title = room.listing.title
            return users, title
        except Room.DoesNotExist:
            return None, None

    @sync_to_async
    def get_room(self, rid):
        try:
            room = Room.objects.get(rid=rid)
            return room, room.seller.uid, room.buyer.uid
        except Room.DoesNotExist:
            return None
        
    @sync_to_async
    def save_message(self, rid, sender_uid, message, timeSent):
        try:
            room = Room.objects.get(rid=rid)
            sender = User.objects.get(uid=sender_uid)
            message = Message.objects.create(sender=sender, content=message, room=room, timeSent=timeSent)
            message.save()
        except (Room.DoesNotExist, User.DoesNotExist):
            raise Exception("Room or user not found")
    