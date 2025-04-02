import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from message.models import Message, Room
from user.models import User
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Check if user is part of the room
        room, seller_uid, buyer_uid = await self.get_room(self.room_name)
        if room is None:
            print(f"Room {self.room_name} does not exist")
            await self.close()
            return

        if self.scope["user"].username not in [seller_uid, buyer_uid]:
            print(f"User {self.scope['user'].username} is not part of room {self.room_name}")
            await self.close()
            return

        print(f"User {self.scope['user'].username} connected to room {self.room_name}")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
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
    
    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({
                "message": event["message"], 
                "sender": event["sender"],
                "timeSent": event["timeSent"].strftime("%Y-%m-%d %H:%M:%S")
            })
        )

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
    